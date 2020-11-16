umapNumNeighbors = Channel.of(25,30)

// inFile = Channel.fromPath("s3://zb4171-monocle/data/cds_droplet_Marrow.rds")
// runMonocleScript = Channel.fromPath('s3://zb4171-monocle/scripts/run_monocle.py')
// extractInfoScript = Channel.fromPath('s3://zb4171-monocle/scripts/extract_info.R')

process runMonocle {
        container 'lee0767/monocle3-cli'
        publishDir 's3://zb4171-monocle/results'
        memory "4GB"

        input:
        file inFile from Channel.fromPath("s3://zb4171-monocle/data/cds_droplet_Marrow.rds")
        file runMonocleScript from Channel.fromPath('s3://zb4171-monocle/scripts/run_monocle.py')
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
        container 'lee0767/monocle3-cli'
        publishDir 's3://zb4171-monocle/results'

        input:
        file extractInfoScript from Channel.fromPath("s3://zb4171-monocle/scripts/extract_info.R")
        file resultFile from resultRdsFiles

        output:
        file "*.csv" into csvFiles
        """
        Rscript ${extractInfoScript} ${resultFile} ${resultFile.getBaseName()}.csv
        """
}
