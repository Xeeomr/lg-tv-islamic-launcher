"""Frozen GUI entry point with an offline packaging check."""
import sys

if __name__ == '__main__':
    if any(flag in sys.argv for flag in ('--check-payload', '--version')):
        from cytv.cli import main
        from cytv.terminal import Console, supports_ansi
        raise SystemExit(main(write=Console(lambda text: print(text) if sys.stdout else None,
                                          interactive=supports_ansi())))
    from cytv.gui import main
    raise SystemExit(main())
