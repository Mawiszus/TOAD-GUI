# Code from https://github.com/Mawiszus/TOAD-GAN
import torch
import torch.nn as nn
from torch.nn.functional import interpolate
import os


# Object containing all important data for a TOAD-GAN
class TOADGAN_obj():
    def __init__(self, Gs, Zs, reals, NoiseAmp, token_list, num_layers):
        self.Gs = Gs
        self.Zs = Zs
        self.reals = reals
        self.NoiseAmp = NoiseAmp
        self.token_list = token_list
        self.num_layers = num_layers


def load_trained_pyramid(gen_path):
    if os.path.exists(gen_path):
        reals = torch.load('%s/reals.pth' % gen_path,
                           map_location="cuda:0" if torch.cuda.is_available() else "cpu")
        Zs = torch.load('%s/noise_maps.pth' % gen_path,
                        map_location="cuda:0" if torch.cuda.is_available() else "cpu")
        NoiseAmp = torch.load('%s/noise_amplitudes.pth' % gen_path,
                              map_location="cuda:0" if torch.cuda.is_available() else "cpu")
        token_list = torch.load('%s/token_list.pth' % gen_path)
        num_layers = torch.load('%s/num_layer.pth' % gen_path)

        Gs = torch.load('%s/generators.pth' % gen_path,
                        map_location="cuda:0" if torch.cuda.is_available() else "cpu")

        toadgan = TOADGAN_obj(Gs, Zs, reals, NoiseAmp, token_list, num_layers)
        msg = 'Model loaded'
    else:
        msg = 'No appropriate Model directory found. Is the path correct?'
        toadgan = TOADGAN_obj(None, None, None, None, None, None)

    return toadgan, msg


# Generates a noise tensor. Uses torch.randn.
def generate_spatial_noise(size, device):
    return torch.randn(size, device=device)


# Generate a sample given a TOAD-GAN and additional parameters
def generate_sample(generators, noise_maps, reals, noise_amplitudes, num_layer, token_list, in_states=None, scale_v=1.0,
                    scale_h=1.0, current_scale=0, gen_start_scale=0, is_bboxed=False, bbox=(0, 0, 0, 0)):

    # in_states holds previously generated outputs for edit mode
    if not in_states or gen_start_scale == 0:
        in_s = None
        images_cur = []
        images = []
        z_s = []
    else:
        images_cur = in_states[0][0:gen_start_scale]
        z_s = in_states[1][0:gen_start_scale]

        images = images_cur
        in_s = None

    # Generate on GPU if available
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    # Main loop
    for G, Z_opt, noise_amp in zip(generators, noise_maps, noise_amplitudes):
        if current_scale >= len(generators):
            break  # should not be reached

        # Zero Padding
        n_pad = int(1 * num_layer)
        m = nn.ZeroPad2d(int(n_pad))

        # Calculate actual shape
        nzx = (Z_opt.shape[2] - n_pad * 2) * scale_v
        nzy = (Z_opt.shape[3] - n_pad * 2) * scale_h

        # Init images list
        images_prev = images_cur
        images_cur = []
        channels = len(token_list)

        # Init in_s
        if in_s is None:
            in_s = torch.zeros(reals[0].shape[0], channels, *reals[0].shape[2:]).to(device)
        elif in_s.sum() == 0:
            in_s = torch.zeros(in_s.shape[0], channels, *in_s.shape[2:]).to(device)

        if current_scale == 0:  # First step: Make base noise
            if is_bboxed:
                if gen_start_scale == 0:
                    z_noise = generate_spatial_noise([1, channels, int(round(nzx)), int(round(nzy))], device=device)
                    z_noise = m(z_noise)
                    z_curr = in_states[1][current_scale]
                    z_curr[0, :, bbox[0] + n_pad:bbox[1] + n_pad, bbox[2] + n_pad:bbox[3] + n_pad] = \
                        z_noise[0, :, bbox[0] + n_pad:bbox[1] + n_pad, bbox[2] + n_pad:bbox[3] + n_pad]
                else:
                    z_curr = in_states[1][current_scale]
            else:
                z_curr = generate_spatial_noise([1, channels, int(round(nzx)), int(round(nzy))], device=device)
                z_curr = m(z_curr)
        else:  # All other steps: Make added noise
            if current_scale < gen_start_scale:
                z_curr = z_s[current_scale]
            else:
                if is_bboxed:
                    if current_scale == gen_start_scale:
                        z_noise = generate_spatial_noise([1, channels, int(round(nzx)), int(round(nzy))], device=device)
                        z_noise = m(z_noise)
                        z_curr = in_states[1][current_scale]
                        z_curr[0, :, bbox[0] + n_pad:bbox[1] + n_pad, bbox[2] + n_pad:bbox[3] + n_pad] = \
                            z_noise[0, :, bbox[0] + n_pad:bbox[1] + n_pad, bbox[2] + n_pad:bbox[3] + n_pad]
                    else:
                        z_curr = in_states[1][current_scale]
                else:
                    z_curr = generate_spatial_noise([1, channels, int(round(nzx)), int(round(nzy))], device=device)
                    z_curr = m(z_curr)

        if (not images_prev) or current_scale == 0:  # if there is no "previous" image
            I_prev = in_s
        else:
            I_prev = images[current_scale-1]

        # Bilinear interpolation for upscaling
        I_prev = interpolate(I_prev, [int(round(nzx)), int(round(nzy))], mode='bilinear', align_corners=False)
        I_prev = m(I_prev)

        # Main Step
        z_in = noise_amp * z_curr + I_prev
        I_curr = G(z_in.detach(), I_prev, temperature=1)

        # Append results
        images_cur.append(I_curr)

        if current_scale >= gen_start_scale:
            images.append(I_curr.detach())
            z_s.append(z_curr.detach())
        current_scale += 1

    return I_curr.detach(), images, z_s
