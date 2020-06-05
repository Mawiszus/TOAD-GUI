# Code based on https://github.com/tamarott/SinGAN
import os
import torch

from .generator import Level_GeneratorConcatSkip2CleanAdd
from .discriminator import Level_WDiscriminator


def weights_init(m):
    """ Init weights for Conv and Norm Layers. """
    classname = m.__class__.__name__
    if classname.find("Conv2d") != -1:
        m.weight.data.normal_(0.0, 0.02)
    elif classname.find("Norm") != -1:
        m.weight.data.normal_(1.0, 0.02)
        m.bias.data.fill_(0)


def init_models(opt):
    """ Initialize Generator and Discriminator. """
    # generator initialization:
    G = Level_GeneratorConcatSkip2CleanAdd(opt).to(opt.device)
    G.apply(weights_init)
    if opt.netG != "":
        G.load_state_dict(torch.load(opt.G))
    print(G)

    # discriminator initialization:
    D = Level_WDiscriminator(opt).to(opt.device)
    D.apply(weights_init)
    if opt.netD != "":
        D.load_state_dict(torch.load(opt.D))
    print(D)

    return D, G


def calc_gradient_penalty(netD, real_data, fake_data, LAMBDA, device):
    # print real_data.size()
    alpha = torch.rand(1, 1)
    alpha = alpha.expand(real_data.size())
    alpha = alpha.to(device)

    interpolates = alpha * real_data + ((1 - alpha) * fake_data)

    interpolates = interpolates.to(device)
    interpolates = torch.autograd.Variable(interpolates, requires_grad=True)

    disc_interpolates = netD(interpolates)

    gradients = torch.autograd.grad(
        outputs=disc_interpolates,
        inputs=interpolates,
        grad_outputs=torch.ones(disc_interpolates.size()).to(device),
        create_graph=True,
        retain_graph=True,
        only_inputs=True,
    )[0]
    gradient_penalty = ((gradients.norm(2, dim=1) - 1) ** 2).mean() * LAMBDA
    return gradient_penalty


def save_networks(G, D, z_opt, opt):
    torch.save(G.state_dict(), "%s/G.pth" % (opt.outf))
    torch.save(D.state_dict(), "%s/D.pth" % (opt.outf))
    torch.save(z_opt, "%s/z_opt.pth" % (opt.outf))


def reset_grads(model, require_grad):
    for p in model.parameters():
        p.requires_grad_(require_grad)
    return model


def load_trained_pyramid(opt, mode_='train'):
    mode = opt.mode
    opt.mode = 'train'
    if (mode == 'animation_train') | (mode == 'SR_train') | (mode == 'paint_train'):
        opt.mode = mode
    dir = opt.out_
    if(os.path.exists(dir)):
        reals = torch.load('%s/reals.pth' % dir)
        Gs = torch.load('%s/generators.pth' % dir)
        Zs = torch.load('%s/noise_maps.pth' % dir)
        NoiseAmp = torch.load('%s/noise_amplitudes.pth' % dir)
        if os.path.exists(dir + '/state_dicts'):
            print('State dicts found! Loading from state dicts!')
            n = len(reals)
            Gs = []
            for i in range(n):
                opt.netG = dir + '/state_dicts/G_%d.pth' % i
                opt.G = dir + '/state_dicts/G_%d.pth' % i
                _, G = init_models(opt)
                # G.load_state_dict(torch.load(dir + '/state_dicts/G_%d.pth' % i))
                # D, G = restore_weights(D, G, i+1, opt)
                G.eval()
                Gs.append(G)

    else:
        print('no appropriate trained model is exist, please train first')
    opt.mode = mode
    return Gs,Zs,reals,NoiseAmp