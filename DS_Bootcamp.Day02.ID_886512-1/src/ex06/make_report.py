from analytics import Research
from config import NUM_OF_PREDS, REPORT_TEMPLATE

if __name__ == '__main__':
    object = Research()
    try:
        total = len(object.file_reader())
        heads, tails = Research.Calculations.counts(object)
        heads_prob, tails_prob = Research.Calculations.fractions(object)
        # Research.Analytics.predict_last(object)
        heads_pred, tails_pred = Research.Analytics.predict_random()

        heads_s = 's' if heads_pred >= 2 else ''
        tails_s = 's' if tails_pred >= 2 else ''

        report = REPORT_TEMPLATE.format(total=total, tails=tails, heads=heads, tails_prob=tails_prob,
                                        heads_prob=heads_prob, num_of_preds=NUM_OF_PREDS, tails_pred=tails_pred,
                                        heads_pred=heads_pred, tails_s=tails_s, heads_s=heads_s)

        Research.Analytics.save_file(report, 'report_file', 'txt')

        object.send_telegram_message("The report has been successfully created.")

    except Exception as e:
        object.send_telegram_message("The report hasn’t been created due to an error.")