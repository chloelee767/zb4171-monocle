params.skipcomparison = false

// umapNumNeighbors = Channel.of(15) // default number of neighbours
umapNumNeighbors = Channel.of(25, 35)

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

process compareResults {
        container 'rocker/r-base:4.0.2'
        publishDir 's3://zb4171-monocle/results/compare/'

        when:
        !params.skipComparison

        input:
        file script from file("s3://zb4171-monocle/scripts/comparison.R")
        file reference from file('s3://zb4171-monocle/results/marrow_umapNN_15.csv')
        file comparison from infoFiles

        output:
        file "*.csv"

        script:
        prefix = "${reference.getBaseName()}_${comparison.getBaseName()}"
        """
        Rscript ${script} ${reference} ${comparison} ${prefix}_graph.csv ${prefix}_partition.csv
        """
}
