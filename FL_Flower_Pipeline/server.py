from Utils.FL_utils import create_server_strategy
from Utils.utils import plot_curve, build_model
import flwr as fl
import pandas as pd
import tensorflow as tf
from pathlib import Path
from collections import defaultdict
import os
import argparse

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'


root_dir = Path(__file__).resolve().parent

# Initialize lists to store training metrics
global_loss, global_accuracy = [], []
client_metrics = defaultdict(lambda: {"loss": [], "accuracy": []})


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Flower")
    parser.add_argument(
        "--fed_alg",
        type=str,
        choices=["FedAvg", "FedProx", "FedMedian", "FedTrimmedAvg", "Krum"],
        default="FedAvg",
        help="Choose the Federated Algorithm from flower documentation. The algorithms implemented in this code are provide in choices field",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        choices=["QUD", "DRED"],
        default="QUD",
        help="Choose the dataset from the options",
    )

    parser.add_argument(
        "--model_name",
        type=str,
        default="test_model4",
        help="Six model are available: ['test_model1', 'test_model2', 'test_model3', 'test_model4', 'test_model5', 'test_model6']",
    )

    parser.add_argument(
        "--pretrained_enabled",
        action="store_true",
        help="Enable pretrained model (default: disabled)."
    )

    parser.add_argument(
        "--stage",
        type=str,
        choices=["Pre", "Post"],
        default="Post",
        help="Choose the training stage from the options for SSFL, pre-deployment or post-deployment.",
    )

    args, _ = parser.parse_known_args()

    print("########################")

    print(f"Pretrained option: {args.pretrained_enabled}")

    num_clients = 3
    num_rounds = 10

    input_shape = (5, )

    if args.stage == "Post":
        args.pretrained_enabled = True
        args.dataset = "HA_Data"
        save_dir = os.path.join(root_dir, "Results",
                                args.dataset, "Server", args.model_name)
    else:
        save_dir = os.path.join(root_dir, "Results",
                                args.dataset, args.fed_alg, "Server", args.model_name)

    os.makedirs(save_dir, exist_ok=True)
    model_path = os.path.join(
        save_dir, f"{args.model_name}_final_global_model.keras")

    if args.pretrained_enabled:
        if os.path.exists(model_path):
            # Load pretrained model
            print(f"Loading global model from {model_path}")
            model = tf.keras.models.load_model(model_path)
        else:
            model = build_model(input_shape,  model_name=args.model_name)
    else:
        model = build_model(input_shape,  model_name=args.model_name)

    print("########################\n")

    strategy = create_server_strategy(fed_strategy=args.fed_alg, client_metrics=client_metrics,
                                      num_clients=num_clients, model=model, global_loss=global_loss, global_accuracy=global_accuracy, dataset=args.dataset)

    config = fl.server.ServerConfig(num_rounds=num_rounds)

    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=config,
        strategy=strategy,
    )

    # Save the final global model
    model.save(os.path.join(
        save_dir, f"{args.model_name}_final_global_model.keras"))

    # Plot and save global training curves
    plot_curve(metrics=global_loss, metrics_name='loss',
               client_name='global', save_dir=save_dir)
    plot_curve(metrics=global_accuracy, metrics_name='accuracy',
               client_name='global', save_dir=save_dir)

    # Plot and save client training curves
    for client_id, metrics in client_metrics.items():
        plot_curve(metrics=metrics["loss"], metrics_name='loss',
                   client_name=f'client_{client_id}', save_dir=save_dir)
        plot_curve(metrics=metrics["accuracy"], metrics_name='accuracy',
                   client_name=f'client_{client_id}', save_dir=save_dir)


if __name__ == "__main__":
    main()
