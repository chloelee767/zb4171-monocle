umapNumNeighbors = Channel.of(50,55)

// inFile = Channel.fromPath("s3://zb4171-monocle/data/cds_droplet_Marrow.rds")
// runMonocleScript = Channel.fromPath('s3://zb4171-monocle/scripts/run_monocle.py')
// extractInfoScript = Channel.fromPath('s3://zb4171-monocle/scripts/extract_info.R')

process runMonocle {
        container 'lee0767/monocle3-cli'
        publishDir 's3://zb4171-monocle/results'
        memory "2GB"

        input:
        file inFile from file("s3://zb4171-monocle/data/cds_droplet_Marrow.rds")
        file runMonocleScript from file("s3://zb4171-monocle/scripts/run_monocle.py")
        val umapNN from umapNumNeighbors

        output:
        file "${outFile}.rds" into resultRdsFiles
        file "${outFile}.json" into resultConfigFiles

        script:
        outFile = "marrow_umapNN_${umapNN}"
        """
        python3 ${runMonocleScript} --input ${inFile} --output ${outFile}.rds --save-config-to ${outFile}.json --reduce-dimension.umap.n-neighbors ${umapNN}
        """
}

process extractInfo {
        container 'quay.io/biocontainers/r-monocle3:0.2.2--r40hc9558a2_0'
        publishDir 's3://zb4171-monocle/results'

        input:
        file extractInfoScript from file("s3://zb4171-monocle/scripts/extract_info.R")
        file resultFile from resultRdsFiles

        output:
        file "*.csv" into infoFiles
        """
        Rscript ${extractInfoScript} ${resultFile} ${resultFile.getBaseName()}.csv
        """
}

// infoFiles.into{ infoFiles1; infoFiles2 }

// referenceFileChannel = infoFiles2.collect()[0]

// process pickReferenceFile {
//         input:
//         file infoFileList from infoFiles.collect()

//         output:
//         file "${infoFileList[0]}" into referenceFileChannel

//         ""
// }

// process pickReferenceFile {
//         container 'rocker/r-base:4.0.2'

//         input:
//         file infoFileList from infoFiles.toSortedList()

//         output:
//         val output into comparisonChannel

//         script:
//         output = [:]
//         reference = infoFileList[0]
//         for (file in infoFileList) {
//             output.put(file, reference)
//         }
//         ""
// }

// comparisonChannel.flatten().buffer(size: 2)

// process compare {
//         container 'rocker/r-base:4.0.2'
//         publishDir 's3://zb4171-monocle/results/compare'

//         input:
//         file comparisonScript from file("s3://zb4171-monocle/scripts/comparison.R")
//         val pair from comparisonChannel

//         output:
//         file "*.csv"

//         script:
//         comparison = pair[0]
//         reference = pair[1]
//         prefix = "${reference.getBaseName()}_${comparison.getBaseName()}"
//         """
//         Rscript ${comparisonScript} ${reference} ${comparison} ${prefix}_graph.csv ${prefix}_partition.csv
//         """
// }
