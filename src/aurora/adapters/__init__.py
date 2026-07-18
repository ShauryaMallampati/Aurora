"""Optional adapters to external multi-agent interfaces."""

__all__ = ["WildfireParallelEnv"]


def __getattr__(name: str):
    if name == "WildfireParallelEnv":
        from .pettingzoo import WildfireParallelEnv

        return WildfireParallelEnv
    raise AttributeError(name)
