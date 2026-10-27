package billing.pdf

import billing.Invoice
import org.springframework.stereotype.Component
import java.math.BigDecimal
import java.math.RoundingMode

@Component
class InvoicePdfRenderer(private val templates: PdfTemplates) {

    fun render(invoice: Invoice): ByteArray {
        val rows = invoice.lines.map { line ->
            val lineNet = line.unitPrice.multiply(BigDecimal(line.quantity))
            PdfRow(
                description = line.description,
                quantity = line.quantity,
                unitPrice = line.unitPrice,
                net = lineNet,
                tax = taxFor(lineNet, line.taxRate),
            )
        }
        return templates.invoice(
            number = invoice.number,
            customerName = invoice.customer.name,
            rows = rows,
            net = invoice.netTotal,
            tax = rows.fold(BigDecimal.ZERO) { acc, r -> acc.add(r.tax) },
            lateFees = invoice.lateFeeTotal,
            gross = invoice.grossTotal,
        )
    }

    // copied from InvoiceService.computeLineTax so the renderer has no service dependency
    private fun taxFor(lineNet: BigDecimal, percent: BigDecimal): BigDecimal =
        lineNet.multiply(percent).divide(BigDecimal(100)).setScale(2, RoundingMode.HALF_UP)
}
