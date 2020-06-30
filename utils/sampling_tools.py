import torch
from torch.distributions.multinomial import Multinomial
from torch.nn.functional import softmax


def get_samples(n_samples, level, bbox=(0, 16, 0, 16), temperature=5,
                use_stats=False, stat_seed=(8, 8), stat_tok_ind=0, curr_token_list=None):
    snippet = level[0, :, bbox[0]:bbox[1], bbox[2]:bbox[3]]
    samples = torch.zeros((n_samples, snippet.shape[0], snippet.shape[1], snippet.shape[2]))
    if use_stats:
        # seed_token_probs = snippet[:, stat_seed[0], stat_seed[1]]
        # seed_token_options = torch.where(seed_token_probs > 0.001)
        # seed_token_ind = seed_token_options[stat_tok_ind]
        stat_windows = torch.load("stat_files/stat_windows_winsize8.pth")
        if not curr_token_list:
            actual_token_list = list(range(snippet.shape[0]))
        else:
            full_token_list = torch.load("stat_files/stat_token_list.pth")
            actual_token_list = ["!" if tok == "Q" else tok for tok in curr_token_list]
            actual_token_list = ["?" if tok == "@" else tok for tok in actual_token_list]
            actual_token_list = [full_token_list.index(tok) for tok in actual_token_list]
        curr_window = stat_windows[stat_tok_ind, actual_token_list]
        winsize = 8
        for w_y in range(-winsize, winsize + 1):
            for w_x in range(-winsize, winsize + 1):
                try:
                    if w_y == 0 and w_x == 0:
                        snippet[:, stat_seed[0]+w_y, stat_seed[1]+w_x] = 0
                        snippet[stat_tok_ind, stat_seed[0]+w_y, stat_seed[1]+w_x] = 1

                    if stat_seed[0] + w_y < 0 or stat_seed[1] + w_x < 0:
                        continue
                    else:
                        snippet[:, stat_seed[0]+w_y, stat_seed[1]+w_x] += curr_window[:, winsize+w_y, winsize+w_x]
                except IndexError:
                    # Outside of window just isn't adjusted
                    continue

    for y in range(snippet.shape[2]):
        for x in range(snippet.shape[1]):
            probs = softmax(snippet[:, x, y] * temperature, dim=0)
            distrib = Multinomial(1, probs=probs)
            samples[:, :, x, y] = distrib.sample((n_samples,))

    return samples


if __name__ == '__main__':
    # Test sampling functions
    lev = torch.ones((1, 5, 30, 30)) * 0.2
    print(lev.shape)
    s = get_samples(10, lev)
    print(s.shape)

