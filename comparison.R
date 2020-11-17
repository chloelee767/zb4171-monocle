arandi <- function(cl1,cl2, adjust=TRUE) {
  # from: https://rdrr.io/cran/mcclust/src/R/arandi.R
  if(length(cl1)!=length(cl2)) stop("cl1 and cl2 must have same length")
  tab.1 <- table(cl1)
  tab.2 <- table(cl2)
  tab.12 <- table(cl1,cl2)
  if(adjust){
    correc <- sum(choose(tab.1,2))*sum(choose(tab.2,2))/choose(length(cl2),2)
    return((sum(choose(tab.12,2))-correc)/(0.5*sum(choose(tab.1,2))+0.5*sum(choose(tab.2,2))-correc) )}
  else{ 
    1+(sum(tab.12^2)-0.5*sum(tab.1^2)-0.5*sum(tab.2^2))/choose(length(cl2),2)
  }
}

sort_by_row_name <- function(df) {
  df[order(row.names(df)),]
}

calculate_arandi <- function(df1, df2) {
  arandi(df1$cluster, df2$cluster)
}

calculate_correlations <- function(df1, df2) {
  df <- data.frame(row.names = c('partition1', 'partition2', 'kendall', 'pearson', 'num_common', 'partition1_size', 'partition2_size'))
  partitions1 <- sort.default(unique(df1$partition))
  partition2 <- sort.default(unique(df2$partition))
  for (p1 in partitions1) {
    for (p2 in partition2) {
      corr_info <- calculate_1_correlation(df1, df2, p1, p2)
      if (corr_info$num_common > 0) {
        df <- rbind(df, data.frame(partition1 = p1, partition2 = p2, corr_info))
      }
    }
  }
  return(df)
}

calculate_1_correlation <- function(df1, df2, partition1, partition2) {
  indices <- which(df1$partition == partition1 & df2$partition == partition2)
  ref_pseudotimes <- df1[indices,]$pseudotime
  comparison_pseudotimes <- df2[indices,]$pseudotime
  
  pearson <- cor(ref_pseudotimes, comparison_pseudotimes, method="pearson")
  kendall <- cor(ref_pseudotimes, comparison_pseudotimes, method="kendall")
  num_common <- length(indices)
  partition1_size = length(which(df1$partition == partition1))
  partition2_size = length(which(df2$partition == partition2))
  return(list(pearson=pearson, kendall=kendall, 
              num_common=num_common, 
              partition1_size=partition1_size, partition2_size=partition2_size))
}

calculate_stats <- function(df1, df2) {
  df1 <- sort_by_row_name(df1)
  df2 <- sort_by_row_name(df2)
  if (any(row.names(df1) != row.names(df2))) {
    stop("cds_info_1 and cds_info_2 contain different rows")
  }
  general_stats <- data.frame(arandi = calculate_arandi(df1, df2))  
  partition_stats <- calculate_correlations(df1, df2)
  
  return(list(general=general_stats, partition=partition_stats))
}

cli.calculate_stats <- function(in.path.cds_info_1, in.path.cds_info_2, out.path.general_stats, out.path.partition_stats) {
  df1 <- read.csv(in.path.cds_info_1, row.names = 1)
  df2 <- read.csv(in.path.cds_info_2, row.names = 1)
  stats <- calculate_stats(df1, df2)
  write.csv(stats$general, out.path.general_stats)
  write.csv(stats$partition, out.path.partition_stats)
}

cmd_args <- commandArgs(trailingOnly = TRUE)
cli.calculate_stats(cmd_args[1], cmd_args[2], cmd_args[3], cmd_args[4])
