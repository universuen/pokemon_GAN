from typing import Iterable
from os import makedirs

from . import config

import torch
from torch import nn
from torchvision.utils import save_image, make_grid
from matplotlib import pyplot as plt


def get_output_size(
        input_size: Iterable[int],
        module: nn.Module
) -> int:
    x = torch.randn(*input_size)
    with torch.no_grad():
        y = module(x)
    return len(y.flatten())


def init_weights(layer: nn.Module):
    layer_name = layer.__class__.__name__
    if 'Conv' in layer_name:
        nn.init.normal_(layer.weight.data, 0.0, 0.02)
    elif layer_name == 'BatchNorm2d':
        nn.init.normal_(layer.weight.data, 1.0, 0.02)
        nn.init.constant_(layer.bias.data, 0)


def train_g_model(
        g_model: torch.nn.Module,
        d_model: torch.nn.Module,
        g_optimizer: torch.optim.Optimizer,
) -> float:
    # clear the generator's gradients
    g_model.zero_grad()

    # prepare a random latent vector
    l_v = torch.randn(
        config.training.batch_size,
        config.data.latent_vector_size,
        1,
        1,
        device=config.device,
    )

    # feed the generator with the latent vector to get fake images
    fake_images = g_model(l_v)

    # feed the discriminator with fake images to get its prediction
    # PS: There is no need to freeze the discriminator's parameters,
    # because the optimizer only is related with the generator, and the
    # discriminator's gradients will be cleared first when it is being trained.
    prediction = d_model(fake_images)

    # calculate the loss
    # PS: The score should be as high as possible, so the higher the score is,
    # the lower the loss will be.
    loss = - prediction.mean()

    # calculate gradients and update weights
    loss.backward()
    g_optimizer.step()

    return loss.item()


def train_d_model(
        d_model: torch.nn.Module,
        g_model: torch.nn.Module,
        real_images: torch.Tensor,
        d_optimizer: torch.optim.Optimizer,
) -> float:
    # The whole workflow is similar with `train_g_model`

    d_model.zero_grad()

    prediction_real = d_model(real_images)
    loss_real = - prediction_real.mean()

    l_v = torch.randn(
        config.training.batch_size,
        config.data.latent_vector_size,
        1,
        1,
        device=config.device,
    )
    fake_images = g_model(l_v).detach()
    prediction_fake = d_model(fake_images)
    loss_fake = prediction_fake.mean()

    loss = loss_real + loss_fake
    loss.backward()
    d_optimizer.step()

    return loss.item()


def denormalize(image: torch.Tensor) -> torch.Tensor:
    return image * 0.5 + 0.5


def save_samples(
        file_name: str,
        samples: torch.Tensor,
):
    makedirs(config.path.training_plots / 'samples', exist_ok=True)
    save_image(
        denormalize(samples),
        str(config.path.training_plots / 'samples' / file_name),
    )


def show_samples(
        samples: torch.Tensor,
):
    plot = make_grid(
        tensor=denormalize(samples)
    ).permute(1, 2, 0)
    plt.imshow(plot)
    plt.show()
    plt.close('all')


def show_image(image: torch.Tensor):
    pass