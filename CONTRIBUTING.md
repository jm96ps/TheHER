# Contributing to TheHER

Thank you for your interest in contributing to **TheHER**! We welcome contributions from electrochemists, materials scientists, software engineers, and students.

## How Can You Contribute?

- **Reporting Bugs**: Open an issue describing the unexpected behavior, including dataset characteristics and the error message.
- **Suggesting Features**: Propose new electrochemical kinetic mechanisms (e.g., OER, HOR, Langmuir vs. Frumkin adsorption isotherms), plotting capabilities, or UI enhancements.
- **Improving Documentation**: Fix typos, clarify physical kinetic assumptions, or write tutorials.
- **Submitting Code**: Fix bugs, optimize fitting algorithms, or add test cases.

---

## Development Setup

1. **Fork and Clone the Repository**:
   ```bash
   git clone https://github.com/jm96ps/TheHER.git
   cd TheHER
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Run the Test Suite**:
   ```bash
   pytest -v
   ```

---

## Pull Request Guidelines

1. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. **Write Unit Tests**: Ensure any new kinetic equations or utility functions are tested in `tests/`.
3. **Verify Existing Tests**: All tests must pass before opening a PR:
   ```bash
   pytest
   ```
4. **Code Style**:
   - Follow [PEP 8](https://peps.python.org/pep-0008/) style conventions.
   - Use meaningful variable names reflecting physical quantities (e.g., `current_density`, `potential_rhe`, `theta_h`).
5. **Open a Pull Request**: Submit the PR against the `main` branch with a clear description of the problem solved.

---

## Code of Conduct

All contributors and participants agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).
