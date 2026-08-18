NUM_OF_PREDS = 3

REPORT_TEMPLATE = (
    'Report\n\nWe have made {total} observations from tossing a coin: {tails} of them were tails and {heads} of them were heads.\nThe probabilities are {tails_prob:.2f}% and {heads_prob:.2f}%, respectively.\nOur forecast is that in the next {num_of_preds} observations we will have: {tails_pred} tail{tails_s} and {heads_pred} head{heads_s}.')
