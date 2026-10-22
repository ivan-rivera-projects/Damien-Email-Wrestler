# Damien Email Wrestler — retired

**This repository is retired.** In October 2026 it was replaced by a rebuild that is
smaller, safer and actually usable:

## → https://github.com/ivan-rivera-projects/damien

This project was four services, three MCP front-ends, two tool registries and forty-nine
tools, with keyword lists standing in for judgement and jobs living in two in-memory dicts.
Its AWS resources (three Lambdas, four DynamoDB tables, an IAM role and its policies) have
been deleted, and nothing of it runs anywhere.

The successor is one package, one binary and one SQLite file:

- rules decide what they can, and Gmail evaluates them itself — a pass costs nothing;
- a model judges only the residue, and only headers and a snippet ever reach it;
- every write is bulk, journalled with its inverse, and reversible with `run undo`;
- `trash` is a label, never a permanent delete, and there is no send path at all;
- it never acts on mail you have not read: a plan takes an approval token to apply.

Nothing here is maintained. The code is kept for history, and this repository is archived.
