This folder contains the full multi-sheet output that BOLD 
generates for the BGE container. Since the container can
gradually grow, the contents in this folder may need to be
updated periodically. When that happens, it may be the case
that there are now additional species that weren't on the
target list. Those are discovered by the bge_load_specimens
process, which emits an addendum.csv file that needs to be
appended to Gap_list_all_updated.csv, e.g. as done 
[here](https://github.com/bge-barcoding/gaplist-data/commit/6d42080ca4e49402dff2e615ae2e559f382d3739)
