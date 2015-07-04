from ecosystem import Ecosystem
import sys


def main():
    eco = Ecosystem()
    eco.execute_args(sys.argv[1:])
