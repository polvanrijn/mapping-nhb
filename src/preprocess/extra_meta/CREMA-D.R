df <- read.csv('/Volumes/Files/Corpora/Corpora/Emotional\ corpus/Accepted/intended/CREMA-D/VideoDemographics.csv')
speakers <- row.names(df)
df <- tidyr::gather(df, new_label, value, Age:Ethnicity)[2:3]
df$new_label <- tolower(df$new_label)
df$value <- stringr::str_replace(stringr::str_replace(df$value, 'Male', 'M'), 'Female', 'F')
df$data_grouping <- 'speaker'
df$key <- speakers
write.csv(df, 'CREMA-D.csv', row.names=F)