import nox


@nox.session(python=["3.10", "3.12"])
def tests(session):
    session.install("-e", ".[dev]")
    session.run("pytest", "-m", "not slow", *session.posargs)


@nox.session
def lint(session):
    session.install("ruff")
    session.run("ruff", "check", "src", "tests")
    session.run("ruff", "format", "--check", "src", "tests")
