from generate_realistic_training_data import generate_good_borrower, compute_features
import pandas as pd

def test_good():
    hits = 0
    for i in range(1, 1000):
        good = generate_good_borrower(i)
        feats = compute_features(good['profile']['transactions'], good['profile']['user_profile'], good['profile']['gst_data'])
        if feats['p2p_circular_loop_flag'] > 0:
            print("Found loop in good borrower!", good['archetype'])
            hits += 1
    print("Total hits:", hits)

if __name__ == '__main__':
    test_good()
