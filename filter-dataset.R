# read command line args
cmdArgs <- commandArgs(trailingOnly = TRUE)
tissue_type <- cmdArgs[1]
matrix_file <- cmdArgs[2]
metadata_file <- cmdArgs[3]
output_file_path <- cmdArgs[4]

## library(dplyr)
library(monocle3)

# load dataset
droplet.mat <- readRDS(matrix_file)
droplet.meta <- read.csv(metadata_file)
row.names(droplet.meta) <- droplet.meta$cell
droplet.gene_meta <- data.frame(gene_short_name = rownames(droplet.mat))
row.names(droplet.gene_meta) <- droplet.gene_meta$gene_short_name
cds <- new_cell_data_set(droplet.mat, cell_metadata = droplet.meta, gene_metadata = droplet.gene_meta)

# filter
cds.filtered <- cds[,colData(cds)$tissue == tissue_type & !is.na(colData(cds)$tissue)]

saveRDS(cds.filtered, file = output_file_path)
