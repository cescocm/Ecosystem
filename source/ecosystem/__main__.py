from ecosystem import Ecosystem


def main():
    eco = Ecosystem()
    args = eco.arg_parser.parse_args()
    eco.execute_args(args)
