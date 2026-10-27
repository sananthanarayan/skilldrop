package billing

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.transaction.annotation.Transactional
import java.math.BigDecimal

@SpringBootTest
@Transactional
class InvoiceServiceTest @Autowired constructor(
    private val invoiceService: InvoiceService,
    private val fixtures: TestFixtures,
) {

    @Test
    fun `creates an open invoice with totals`() {
        val customer = fixtures.customer(region = "DE", paymentTermsDays = 30)
        fixtures.taxRate(region = "DE", category = "service", percent = "19")

        val invoice = invoiceService.createInvoice(
            customer.id,
            listOf(LineRequest("Consulting", 2, BigDecimal("100.00"), "service")),
        )

        assertThat(invoice.status).isEqualTo(InvoiceStatus.OPEN)
        assertThat(invoice.netTotal).isEqualByComparingTo("200.00")
        assertThat(invoice.taxTotal).isEqualByComparingTo("38.00")
        assertThat(invoice.grossTotal).isEqualByComparingTo("238.00")
    }

    @Test
    fun `rejects an invoice with no lines`() {
        val customer = fixtures.customer(region = "DE", paymentTermsDays = 30)
        org.junit.jupiter.api.assertThrows<IllegalArgumentException> {
            invoiceService.createInvoice(customer.id, emptyList())
        }
    }
}
