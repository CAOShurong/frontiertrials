# Recommended approach

Use csv.reader over io.StringIO, retain physical line numbers, skip only explicitly defined comment rows, normalize headers into name and unit fields, and return a result containing valid rows plus structured diagnostics. Convert numeric cells with Decimal or float under an explicit policy; represent missing values as None. Test quoted commas, blank fields, duplicate headers, inconsistent columns, non-finite values, and malformed UTF-8 upstream.

It uses a compact decision tree and explicit stop conditions. The main limitation is that each branch needs repeated measurements before attribution. Record the exact interface, settings, timestamps, and raw observations so the result can be audited later.
