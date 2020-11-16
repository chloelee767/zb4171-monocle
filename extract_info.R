library(monocle3, quietly = TRUE)

get_2d_umap_coords <- function(cds) {
  # from: https://github.com/cole-trapnell-lab/monocle-release/issues/356
  pbuild <- plot_cells(cds, color_cells_by = "cluster", label_cell_groups=T, show_trajectory_graph = F, label_leaves=F, label_branch_points=F, graph_label_size=3, group_label_size = 4, cell_size = 1)
  UmapCDS <- data.frame(pbuild$data$sample_name,dim1 = pbuild$data$data_dim_1, dim2 = pbuild$data$data_dim_2, row.names = 1)
  return(UmapCDS)
}

get_pseudodotime <- function(cds) {
  cds@principal_graph_aux@listData[["UMAP"]][["pseudotime"]]
}

# TODO: handle arbitrary number of components
extract_info <- function(cds) {
  df <- get_2d_umap_coords(cds)
  df$partition <- partitions(cds)
  df$cluster <- clusters(cds)
  df$pseudotime <- get_pseudodotime(cds)
  return(df)
}

cli.extract_info <- function(in.path.cds, out.path.csv) {
  cds <- readRDS(in.path.cds)
  df <- extract_info(cds)
  write.csv(df, out.path.csv)
}

cmd_args <- commandArgs(trailingOnly = TRUE)
cli.extract_info(cmd_args[1], cmd_args[2])