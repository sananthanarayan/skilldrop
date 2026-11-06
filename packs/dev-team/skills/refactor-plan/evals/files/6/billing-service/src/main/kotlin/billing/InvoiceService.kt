package billing

import jakarta.persistence.EntityManager
import jakarta.persistence.PersistenceContext
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import java.math.BigDecimal
import java.math.RoundingMode
import java.time.Clock
import java.time.LocalDate

@Service
class InvoiceService(
    private val invoiceRepository: InvoiceRepository,
    private val taxRateRepository: TaxRateRepository,
    private val customerRepository: CustomerRepository,
    private val clock: Clock,
) {

    @PersistenceContext
    private lateinit var em: EntityManager

    // ---------------------------------------------------------------
    // Creation
    // ---------------------------------------------------------------

    @Transactional
    fun createInvoice(customerId: Long, lines: List<LineRequest>): Invoice {
        val customer = customerRepository.findById(customerId)
            .orElseThrow { IllegalArgumentException("unknown customer $customerId") }
        require(lines.isNotEmpty()) { "invoice needs at least one line" }

        val invoice = Invoice(
            customer = customer,
            issuedOn = LocalDate.now(clock),
            dueOn = LocalDate.now(clock).plusDays(customer.paymentTermsDays.toLong()),
            status = InvoiceStatus.OPEN,
        )
        lines.forEach { req ->
            val rate = taxRateRepository.findByRegionAndCategory(customer.region, req.category)
                ?: taxRateRepository.findDefault(customer.region)
            invoice.lines.add(
                InvoiceLine(
                    invoice = invoice,
                    description = req.description,
                    quantity = req.quantity,
                    unitPrice = req.unitPrice,
                    taxRate = rate.percent,
                )
            )
        }
        recalculate(invoice)
        return invoiceRepository.save(invoice)
    }

    // ---------------------------------------------------------------
    // Totals and tax
    // ---------------------------------------------------------------

    fun recalculate(invoice: Invoice) {
        var net = BigDecimal.ZERO
        var tax = BigDecimal.ZERO
        invoice.lines.forEach { line ->
            val lineNet = line.unitPrice.multiply(BigDecimal(line.quantity))
            net = net.add(lineNet)
            tax = tax.add(computeLineTax(lineNet, line.taxRate))
        }
        invoice.netTotal = net.setScale(2, RoundingMode.HALF_EVEN)
        invoice.taxTotal = tax
        invoice.grossTotal = invoice.netTotal.add(invoice.taxTotal).add(invoice.lateFeeTotal)
    }

    // Tax is rounded per line (HALF_EVEN), not on the invoice total.
    // Finance signed this off in 2023; do not change without them.
    fun computeLineTax(lineNet: BigDecimal, percent: BigDecimal): BigDecimal =
        lineNet.multiply(percent).divide(BigDecimal(100)).setScale(2, RoundingMode.HALF_EVEN)

    // ---------------------------------------------------------------
    // Overdue and late fees
    // ---------------------------------------------------------------

    fun findOverdue(asOf: LocalDate): List<Invoice> =
        em.createQuery(
            "select i from Invoice i join fetch i.customer " +
                "where i.status in (:open, :dunning) and i.dueOn < :asOf",
            Invoice::class.java,
        )
            .setParameter("open", InvoiceStatus.OPEN)
            .setParameter("dunning", InvoiceStatus.IN_DUNNING)
            .setParameter("asOf", asOf)
            .resultList

    @Transactional
    fun applyLateFees(asOf: LocalDate): Int {
        var count = 0
        findOverdue(asOf).forEach { invoice ->
            val daysLate = asOf.toEpochDay() - invoice.dueOn.toEpochDay()
            if (daysLate < invoice.customer.lateFeeGraceDays) return@forEach
            if (invoice.customer.lateFeeExempt) return@forEach

            val fee = invoice.netTotal
                .multiply(BigDecimal("0.015"))
                .multiply(BigDecimal(daysLate / 30 + 1))
                .setScale(2, RoundingMode.HALF_UP)
            if (fee > invoice.lateFeeTotal) {
                invoice.lateFeeTotal = fee
                recalculate(invoice)
                em.merge(invoice)
                count++
            }
        }
        return count
    }

    // ---------------------------------------------------------------
    // Payment
    // ---------------------------------------------------------------

    @Transactional
    fun markPaid(invoiceId: Long, amount: BigDecimal, paidOn: LocalDate) {
        val invoice = invoiceRepository.findById(invoiceId)
            .orElseThrow { IllegalArgumentException("unknown invoice $invoiceId") }
        check(invoice.status != InvoiceStatus.VOID) { "cannot pay a void invoice" }

        invoice.amountPaid = invoice.amountPaid.add(amount)
        if (invoice.amountPaid >= invoice.grossTotal) {
            invoice.status = InvoiceStatus.PAID
            invoice.paidOn = paidOn
        }
        // native update keeps the customer balance in step; the ORM mapping
        // for Customer.balance is read-only (see V31__customer_balance.sql)
        em.createNativeQuery(
            "update customer set balance = balance - :amount where id = :id"
        )
            .setParameter("amount", amount)
            .setParameter("id", invoice.customer.id)
            .executeUpdate()
        invoiceRepository.save(invoice)
    }

    @Transactional
    fun void(invoiceId: Long, reason: String) {
        val invoice = invoiceRepository.findById(invoiceId)
            .orElseThrow { IllegalArgumentException("unknown invoice $invoiceId") }
        check(invoice.amountPaid.signum() == 0) { "cannot void a part-paid invoice" }
        invoice.status = InvoiceStatus.VOID
        invoice.voidReason = reason
        invoiceRepository.save(invoice)
    }
}

data class LineRequest(
    val description: String,
    val quantity: Int,
    val unitPrice: BigDecimal,
    val category: String,
)
