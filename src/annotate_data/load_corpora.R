# Title     : load corpora
# Created by: pol.van-rijn
# Created on: 18.09.20

.filenames_to_meta <- function(names) {
      #' Convert filenames to variables
      #'
      #' Converts the filenames into the variables corpus, sentence, speaker, repetition, intensity and emotion
      #'
      #' @param names list of filenames
      #' @return
      #' @examples
      #' .filenames_to_meta(c("'AH1_HAP_AEB_AA_A_XX.wav'", "'AH1_NEU_AAJ_AA_A_XX.wav'", "'AH1_SUR_ADZ_AA_A_XX.wav'"))
      #' # Yields:
      #' #    corpus sentence speaker repetition intensity emotion
      #' # 1    AH1  AH1_AEB  AH1_AA          1      <NA>     HAP
      #' # 2    AH1  AH1_AAJ  AH1_AA          1      <NA>     NEU
      #' # 3    AH1  AH1_ADZ  AH1_AA          1      <NA>     SUR
  split_filename <- stringr::str_split_fixed(as.character(names), "_", 6)
  corpus_names <- stringr::str_remove_all(split_filename[, 1], "'")
  data.frame(
    corpus = corpus_names,

    # Add the corpus name, because speaker 1 in corpus A is not speaker 1 in corpus B
    sentence = paste(corpus_names, split_filename[, 3], sep = '_'),
    speaker = paste(corpus_names, split_filename[, 4], sep = '_'),

    # convert to number
    repetition = match(split_filename[, 5], LETTERS),

    # ordinal variable: LO < MI < HI, if no intensity specified: NA
    intensity = factor(stringr::str_remove(split_filename[, 6], ".wav'"), levels = c("LO", "MI", "HI"), order = TRUE),

    # Emotion
    emotion = split_filename[, 2]
  )
}

load_corpora <- function(emotions, feature_set, csv_dir, scale_center = TRUE, fully_balanced = TRUE) {
      #' Load corpora
      #'
      #' Loads features of corpora from a directory
      #'
      #' @param emotions list of emotions that will be extracted.
      #' @param feature_set the used feature set (only eGeMAPS is supported).
      #' @param csv_dir the directory containing all CSVs.
      #' @param scale_center scale and center each feature, default TRUE.
      #' @param fully_balanced if true, each corpus contains all of the specified emotions, i.e. corpora are excluded from.
      #' the selection if they do not contain all emotions. If false, we'll extract the available subset. Say we want to
      #' extract basic emotions, but a corpus contains sarcasm, neutral and sad, we'll only extract neutral and sad.
      #' @return
      #' @examples
      #' load_corpora(EMOTIONS, 'eGeMAPS', '../../data/csv/', fully_balanced = F)

  # Currently only eGeMAPS supported
  emotion_str <- paste(emotions, collapse = ', ')
  if (feature_set != 'eGeMAPS') {
    stop('Feature set not supported')
  }

  # Concatenate all df
  df <- NULL
  meta <- NULL
  for (f in list.files(csv_dir)) {
    # Only look at csv files
    if (stringr::str_ends(f, paste0('_', feature_set, '.csv'))) {
      corpus_df <- read.csv(paste0(csv_dir, f), sep = ';')
      corpus_meta <- .filenames_to_meta(corpus_df$name)
      corpus_meta$filename <- corpus_df$name
      if (fully_balanced) {
        if (all(emotions %in% unique(corpus_meta$emotion))) {
          # Only proceed if contains all emotions
          df <- rbind(df, corpus_df)
          meta <- rbind(meta, corpus_meta)
        } else {
          corpus_name <- stringr::str_split(f, '_')[[1]][1]
          print(paste('Skip', corpus_name, 'because it does not contain all specified emotions:', emotion_str))
        }
      } else {
        # If we don't care about balancing, just add them
        df <- rbind(df, corpus_df)
        meta <- rbind(meta, corpus_meta)
      }
    }
  }

  # Remove first two columns in eGeMAPS feature set
  if (feature_set == 'eGeMAPS') {
    SKIP_FIRST_N_COLS <- 2
  }
  print(paste('Removing not data columns:', paste(names(df)[1:SKIP_FIRST_N_COLS], collapse = ', ')))

  # Subset the data
  X <- df[, (SKIP_FIRST_N_COLS + 1):ncol(df)]

  # Scale and center
  if (scale_center) {
    X <- scale(X)
  }

  # Filter by emotion
  print(paste('Only selecting the emotions: ', emotion_str))
  idx <- meta$emotion %in% emotions
  meta <- meta[idx,]
  X <- X[idx,]

  if (fully_balanced) {
    # Assert that every emotion is really present
    emotions_per_corpus <- meta %>%
      group_by(corpus) %>%
      summarise(n_emo = length(unique(emotion)))

    if (!all(emotions_per_corpus$n_emo == length(emotions))) {
      stop(paste('Not all corpora contain the specified emotions:', emotion_str))
    }
  }


  # Convert to factors
  meta$corpus <- as.factor(meta$corpus)
  meta$sentence <- as.factor(meta$sentence)
  meta$speaker <- as.factor(meta$speaker)
  meta$emotion <- droplevels(as.factor(meta$emotion))

  # Print a summary of all emotions and corpora loaded + total number of fragments
  print(paste0(emotion_str, ', total corpora:', length(unique(meta$corpus)), ', total fragments:', nrow(meta)))
  list(X = X, meta = meta)
}


# Some helper functions
.num_to_letter <- function(number) {
  number <- (number - 1) %% 26
  LETTERS[number + 1]
}

.num_to_two_letters <- function(number) {
  if (number > 26^2) {
    stop(paste('The allowed domain is 1 to', 26^2))
  }
  first_letter <- .num_to_letter(ceiling(number / 26))
  second_letter <- .num_to_letter(number)
  paste0(first_letter, second_letter)
}

.num_to_three_letters <- function(number) {
  if (number > 26^3) {
    stop(paste('The allowed domain is 1 to', 26^3))
  }
  scalar <- ceiling(number / 26^2)
  first_letter <- .num_to_letter(scalar)
  second_third_letter <- .num_to_two_letters(number - ((scalar - 1) * 26^2))
  paste0(first_letter, second_third_letter)
}

process_sex <- function(all_data, extra_meta) {
  all_speakers <- unique(all_data$speaker)
  label_meta <- filter(extra_meta, new_label == "sex")
  label_meta$speaker <- unlist(lapply(as.numeric(label_meta$key), .num_to_two_letters))
  label_meta$speaker <- paste(label_meta$corpus, label_meta$speaker, sep = '_')
  if (!all(all_speakers %in% label_meta$speaker)) {
    stop('All speakers need to be represented!')
  }
  relevant_data <- label_meta[c('value', 'speaker')]
  names(relevant_data)[1] <- "sex"
  merge(relevant_data, all_data, by.x = 'speaker', by.y = 'speaker')
}

.compare_dfs <- function (df1, df2, decim=5, n_factor=7){
  df1_sorted <- df1 %>% arrange(filename)
  df2_sorted <- df2 %>% arrange(filename)

  all_same <- TRUE
  for (f in 1:n_factor){
    col_n <- paste0('RC', f)
    comp <- all(round(df1_sorted[col_n], decim) == round(df2_sorted[col_n], decim))
    if (!comp){
      print(col_n)
    }
    all_same <- all_same & comp
  }
  all_same
}