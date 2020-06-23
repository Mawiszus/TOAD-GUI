import torch
from torch.distributions.multinomial import Multinomial
from torch.nn.functional import softmax


def get_samples(n_samples, level, bbox=(0, None, 0, None), temperature=5):
    snippet = level[0, :, bbox[0]:bbox[1], bbox[2]:bbox[3]]
    samples = torch.zeros((n_samples, snippet.shape[0], snippet.shape[1], snippet.shape[2]))
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

