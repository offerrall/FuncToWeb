# Prefill: from the query parameter to the plan

What happens between the `prefill` query parameter and the HTML that is served.
The contract — the two entry points, the error tables, what is base and what is
temporary — is in [prefill.md](../prefill.md).

## The walk

From the query parameter to the plan: `json.loads()` runs, the root is verified
to be an object, `decode()` prepares the transport, and a temporary partial
`Signature` (containing only the parameters present) builds them with `build()`,
producing exact Python values. Those values go into `page_of()`, which generates
the plan and the HTML. The Python entry point starts directly at the last step.
