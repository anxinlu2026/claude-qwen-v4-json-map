# Resources

Search here first for anything that can serve as a reference for a design. In the agent container
this folder is `/opt/resources`. Each sub-folder has its own `INDEX.md`.

| Folder | Holds | Use |
|---|---|---|
| `standards/` | Published standards, stored as obtained from the publisher | The definition of a function; the values it prints are trusted |
| `ip_models/` | Models of functions, each with a validation that can be run | Golden values, after its validation passes |
| `reference_tools/` | Established implementations installed in the container | An independent source to validate a model against |

If no model exists here for the function and one must be built:
1. Read the standard that defines the function and write the model step by step from it, not from memory.
2. Before it is used, its outputs must agree with the task's testbench values or with a reliable
   established implementation (`reference_tools/`). A model that has not passed is not golden.
