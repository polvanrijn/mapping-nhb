# Title     : Combine the preprocessed data in to RDS files
# Created by: pol.van-rijn
# Created on: 09.10.20

library(dplyr)

# Load the meta data
extra_corpus_meta_df <- readRDS('corpus_meta.RDS')

# Load the corpora
source('load_corpora.R')
EMOTIONS <- c("ANG", "DIS", "FER", "HAP", "SAD", "SUR", "NEU")
#out = load_corpora(EMOTIONS, 'eGeMAPS', '../../data/csv/')
out_all <- load_corpora(EMOTIONS, 'eGeMAPS', '../../data/csv/', fully_balanced = F)

# Compute the factor analysis
n_factor <- 7
fa <- suppressWarnings(psych::principal(out_all$X, nfactors = n_factor, rotate = 'varimax'))


# Get the hofstede dimensions
hofstede_sel <- read.csv('dimensions/hofstede/hofstede-insights.csv') %>%
  mutate(country = stringr::str_remove(country, '\\*'))

# Read datapoints from Inglehart-Welzel Culture Map 2017:
# https://commons.wikimedia.org/wiki/File:Culture_Map_2017_conclusive.png
IW <- read.csv('dimensions/inglehart–welzel/IW_extracted.csv')
# IMPORTANT MODIFICATIONS: Assumptions: Singapore ≈ China, Kenya ≈ Ethiopia
IW <- rbind(
  IW,
  filter(IW, country == 'China') %>% mutate(country = 'Singapore'), # Singapore -> China
  filter(IW, country == 'Ethiopia') %>% mutate(country = 'Kenya') # Kenya -> Ethiopia
)

available_languages <- unique(read.csv('dimensions/elinguistics/distances_sparse_elinguistics.csv')$language1)


# Function
construct_df <- function(out) {
  meta <- out$meta
  X <- out$X

  # Make sure NEU is reference
  meta[['emotion']] <- factor(meta[['emotion']], levels = c("NEU", "ANG", "DIS", "FER", "HAP", "SAD", "SUR"))

  # Predict into factor space
  predict_X <- data.frame(predict(fa, X))
  names(predict_X) <- paste0("RC", 1:n_factor)

  # Scale factors
  predict_X <- scale(predict_X)

  dat_list <- cbind(predict_X, meta)

  # Insert extra corpus meta data
  dat_list <- merge(dat_list, extra_corpus_meta_df, by.x = 'corpus', by.y = 'name_short')

  # Add metadata from specific corpora
  extra_meta <- rbind(
    read.csv('../../src/preprocess/extra_meta/AHOEMO1.csv', colClasses = c("character")) %>% mutate(corpus = 'AH1'), # 1
    read.csv('../../src/preprocess/extra_meta/AHOEMO2.csv', colClasses = c("character")) %>% mutate(corpus = 'AH2'), # 2
    read.csv('../../src/preprocess/extra_meta/CaFE.csv', colClasses = c("character")) %>% mutate(corpus = 'CFE'), # 3
    read.csv('../../src/preprocess/extra_meta/CREMA-D.csv', colClasses = c("character")) %>% mutate(corpus = 'CRE'), # 4
    read.csv('../../src/preprocess/extra_meta/DaFEX.csv', colClasses = c("character")) %>% mutate(corpus = 'DAF'), # 5
    read.csv('../../src/preprocess/extra_meta/DB_Arabic.csv', colClasses = c("character")) %>% mutate(corpus = 'DBA'), # 6
    read.csv('../../src/preprocess/extra_meta/EMO-DB.csv', colClasses = c("character")) %>% mutate(corpus = 'EDB'), # 7
    read.csv('../../src/preprocess/extra_meta/EEKK.csv', colClasses = c("character")) %>% mutate(corpus = 'EEK'), # 8
    read.csv('../../src/preprocess/extra_meta/EmoHI.csv', colClasses = c("character")) %>% mutate(corpus = 'EHI'), # 9
    read.csv('../../src/preprocess/extra_meta/EMA.csv', colClasses = c("character")) %>% mutate(corpus = 'EMA'), # 10
    read.csv('../../src/preprocess/extra_meta/eNTERFACE.csv', colClasses = c("character")) %>% mutate(corpus = 'ENT'), # 11
    read.csv('../../src/preprocess/extra_meta/ESCAD.csv', colClasses = c("character")) %>% mutate(corpus = 'ESC'), # 12
    read.csv('../../src/preprocess/extra_meta/GEMEP.csv', colClasses = c("character")) %>% mutate(corpus = 'GEM'), # 13
    read.csv('../../src/preprocess/extra_meta/MAP_HAWK.csv', colClasses = c("character")) %>% mutate(corpus = 'HAW'), # 14
    read.csv('../../src/preprocess/extra_meta/MSP_improv.csv', colClasses = c("character")) %>% mutate(corpus = 'IMP'), # 15
    read.csv('../../src/preprocess/extra_meta/JUSLIN_LAUKKA_2001.csv', colClasses = c("character")) %>% mutate(corpus = 'J01'), # 16
    read.csv('../../src/preprocess/extra_meta/PAX.csv', colClasses = c("character")) %>% mutate(corpus = 'PAX'), # 17
    read.csv('../../src/preprocess/extra_meta/RAVDESS.csv', colClasses = c("character")) %>% mutate(corpus = 'RAV'), # 18
    read.csv('../../src/preprocess/extra_meta/SAVEE.csv', colClasses = c("character")) %>% mutate(corpus = 'SAV'), # 19
    read.csv('../../src/preprocess/extra_meta/IITKGP-SESC.csv', colClasses = c("character")) %>% mutate(corpus = 'SES'), # 20
    read.csv('../../src/preprocess/extra_meta/IITKGP-SEHSC.csv', colClasses = c("character")) %>% mutate(corpus = 'SEH'), # 21
    read.csv('../../src/preprocess/extra_meta/TESS.csv', colClasses = c("character")) %>% mutate(corpus = 'TES'), # 22
    read.csv('../../src/preprocess/extra_meta/EmoV-DB.csv', colClasses = c("character")) %>% mutate(corpus = 'VDB'), # 23
    read.csv('../../src/preprocess/extra_meta/VENEC.csv', colClasses = c("character")) %>% mutate(corpus = 'VEN') # 24
  )
  dat_list <- process_sex(dat_list, extra_meta)

  # PAX fix pseudosentence
  if ('PAX' %in% dat_list$corpus) {
    row_idx <- dat_list$corpus == 'PAX'
    is_pseudo <- function(x) as.numeric(substr(x, 1, 1) == 'Z')
    PAX_sentences <- stringr::str_remove(dat_list[row_idx, 'sentence'], 'PAX_')
    dat_list[row_idx, 'pseudo_speech'] <- unlist(lapply(PAX_sentences, is_pseudo))
  }

  # J01 fix language: either swedish or english
  if ('J01' %in% dat_list$corpus) {
    J01_df <- filter(extra_meta, corpus == 'J01', new_label == 'language')
    J01_df$speaker <- unlist(lapply(as.numeric(J01_df$key), .num_to_two_letters))
    J01_df$speaker <- paste(J01_df$corpus, J01_df$speaker, sep = '_')
    J01_df$language <- J01_df$value
    for (r in 1:nrow(J01_df)) {
      row_idx <- as.character(dat_list$speaker) == J01_df[r, "speaker"]
      dat_list[row_idx, "language"] <- J01_df[r, "language"]
    }
  }

  # VENEC fix country
  if ('VEN' %in% dat_list$corpus) {
    VEN_df <- filter(extra_meta, corpus == 'VEN', new_label == 'country')
    VEN_df$country <- plyr::revalue(VEN_df$value, c("AU" = "Australia", "IN" = "India", "KE" = "Kenya", "SI" = "Singapore", "US" = "United States"))
    VEN_df$speaker <- unlist(lapply(as.numeric(VEN_df$key), .num_to_two_letters))
    VEN_df$speaker <- paste(VEN_df$corpus, VEN_df$speaker, sep = '_')

    for (r in 1:nrow(VEN_df)) {
      row_idx <- as.character(dat_list$speaker) == VEN_df[r, "speaker"]
      dat_list[row_idx, "country"] <- VEN_df[r, "country"]
    }
  }

  # Check if all countries are present!
  listed_countries <- sort(unique(dat_list$country))
  if (!all(listed_countries %in% IW$country)) {
    stop('Country mismatch between IW and table!')
  }

  if (!all(listed_countries %in% hofstede_sel$country)) {
    stop('Country mismatch between Hofstede and table!')
  }

  # Check if all languages are present!
  listed_languages <- sort(unique(dat_list$language))
  if (!all(listed_languages %in% available_languages)){
    stop('Some languages are missing')
  }

  # Add hofstede dimensions
  dat_list <- merge(dat_list, hofstede_sel, by.x = 'country', by.y = 'country', all.x = T)

  # Add IW dimensions
  dat_list <- merge(dat_list, IW, by.x = 'country', by.y = 'country', all.x = T)

  print('NA report:')
  print(apply(dat_list, 2, function (x) length(which(is.na(x)))))

  dat_list
}

saveRDS(
  construct_df(out_all),
  '../../data/data_all.RDS'
)
