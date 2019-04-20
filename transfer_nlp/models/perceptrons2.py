import logging

import torch
import torch.nn as nn
import torch.nn.functional as F

from transfer_nlp.common.utils import describe
from transfer_nlp.loaders.vectorizers import Vectorizer
from transfer_nlp.plugins.config import register_plugin
from transfer_nlp.plugins.registry import register_model

name = 'transfer_nlp.models.perceptrons'
logging.getLogger(name).setLevel(level=logging.INFO)
logger = logging.getLogger(name)
logging.info('')


@register_plugin
class Perceptron2(nn.Module):

    def __init__(self, num_features):

        super().__init__()
        self.fc = nn.Linear(in_features=num_features, out_features=2)

    def forward(self, x_in: torch.Tensor, apply_sigmoid: bool = False) -> torch.Tensor:
        """
        Linear transformation, and squeeze to get only batch direction
        :param x_in: size (batch, num_features)
        :param apply_sigmoid: False if used with the cross entropy loss, True if probability wanted
        :return:
        """

        y_out = self.fc(x_in).squeeze()
        if apply_sigmoid:
            y_out = F.sigmoid(y_out)

        return y_out


@register_model
class MultiLayerPerceptron2(nn.Module):

    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int):
        super().__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

        self.fc = nn.Linear(in_features=input_dim, out_features=hidden_dim)
        self.fc2 = nn.Linear(in_features=hidden_dim, out_features=output_dim)
        # TODO: experiment with more layers

    def forward(self, x_in: torch.Tensor, apply_softmax: bool = False) -> torch.Tensor:
        """
        Linear -> ReLu -> Linear (+ softmax if probabilities needed)
        :param x_in: size (batch, input_dim)
        :param apply_softmax: False if used with the cross entropy loss, True if probability wanted
        :return:
        """
        # TODO: experiment with other activation functions

        intermediate = F.relu(self.fc(x_in))
        output = self.fc2(intermediate)

        if self.output_dim == 1:
            output = output.squeeze()

        if apply_softmax:
            output = F.softmax(output, dim=1)

        return output


def predict_mlp(input_string: str, model: nn.Module, vectorizer: Vectorizer):
    """
    Do inference from a text review
    :param input_string:
    :param model:
    :param vectorizer:
    :return:
    """

    vector = torch.tensor(vectorizer.vectorize(input_string=input_string))
    classifier = model.cpu()
    result = classifier(vector.view(1, -1))#.unsqueeze(dim=0)

    _, result = result.max(dim=1)
    result = int(result[0])

    return vectorizer.target_vocab.lookup_index(index=result)


def inspect_model(model: nn.Module, vectorizer: Vectorizer):
    """
    Check the extreme words (positives and negatives) for linear binary classification models
    :param model:
    :param vectorizer:
    :return:
    """

    fc_weights = model.fc.weight.detach()[0]
    _, indices = torch.sort(fc_weights, dim=0, descending=True)
    print(fc_weights.shape)
    indices = indices.numpy().tolist()

    logger.info("#"*50)
    logger.info("Top positive words:")
    logger.info("#"*50)
    for i in range(20):
        logger.info(vectorizer.data_vocab.lookup_index(index=indices[i]))

    logger.info("#"*50)
    logger.info("Top negative words:")
    logger.info("#"*50)
    indices.reverse()
    for i in range(20):
        logger.info(vectorizer.data_vocab.lookup_index(index=indices[i]))


if __name__ == "__main__":

    batch_size = 32
    num_features = 100

    model = Perceptron(num_features=num_features)

    tensor = torch.randn(size=(batch_size, num_features))
    describe(tensor)
    output = model.forward(x_in=tensor)
    describe(x=output)


    input_dim = 10
    hidden_dim = 10
    output_dim = 10

    model = MultiLayerPerceptron(input_dim=input_dim, hidden_dim=hidden_dim, output_dim=output_dim)

    tensor = torch.randn(size=(batch_size, input_dim))
    describe(tensor)
    output = model(x_in=tensor)
    describe(x=output)