r117's proof: tools/check_racine_safari.py --extract prints the same before (HEAD 3070922) and after
over_file's split. Logs made by `python3 tools/r113/extract_same.py make LOGS` (not kept: rebuild
them), read by `... run TREE LOGS OUT` for each tree; `diff -r before after` is empty.
