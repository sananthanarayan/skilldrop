package billing

import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Component
import org.springframework.transaction.annotation.Transactional
import java.time.Clock
import java.time.LocalDate

@Component
class DunningJob(
    private val invoiceService: InvoiceService,
    private val notifier: DunningNotifier,
    private val clock: Clock,
) {

    @Scheduled(cron = "0 0 6 * * *")
    @Transactional
    fun run() {
        val today = LocalDate.now(clock)
        invoiceService.applyLateFees(today)

        invoiceService.findOverdue(today).forEach { invoice ->
            invoice.status = InvoiceStatus.IN_DUNNING
            invoice.dunningLevel = invoice.dunningLevel + 1
            invoice.lastDunnedOn = today
            notifier.send(invoice.customer, invoice, invoice.dunningLevel)
        }
    }
}
