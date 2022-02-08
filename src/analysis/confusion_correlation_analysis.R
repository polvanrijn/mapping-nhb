library(dplyr)

# Settings
ADD_GLOBAL_MAPPING <- T
EMOTIONS <- c("ANG", "DIS", "FER", "HAP", "SAD", "SUR")

# Load posterior samples and the data
params <- readRDS('../../results/models/params/params_big_model.RDS')
data <- readRDS('../../data/data_all.RDS')

# Rename culture
data$culture <- stringr::str_replace_all(paste0(data$country, '_', data$language), ' ', '.')
names(params) <- stringr::str_replace_all(names(params), 'country:language', 'culture')

# Stores which emotions are available for each culture
culture_emotion_lookup <- list()
for (cult in unique(data$culture)) {
  sub_list <- list()
  for (emo in EMOTIONS) {
    sub_list[[emo]] <- nrow(filter(data, emotion == emo, culture == cult)) != 0
  }
  culture_emotion_lookup[[cult]] <- sub_list
}


get_cor_vector <- function(key, value, emo) {
  stopifnot(key %in% c('culture', 'sex', 'speaker'))
  return_vect <- c()
  # Goes through all coeefficients and sums the global RC coefficient on top of the speaker, sex, or culture specific
  # RC coefficient
  # The coefficient estimates are concatenated. Since we have 4000 predictions per coefficient, the function will return
  # 7 * 4000 = 28,000 samples
  for (RC in paste0('RC', 1:7)) {
    estimates <- params[[paste0('r_', key, '__mu', emo, '[', value, ',', RC, ']')]]
    if (ADD_GLOBAL_MAPPING) {
      estimates <- estimates + params[[paste0('b_mu', emo, '_', RC)]]
    }
    return_vect <- c(return_vect, estimates)
  }
  return_vect
}


culture_results <- NULL
for (emo1 in EMOTIONS) {
  for (cult1 in unique(data$culture)) {
    if (culture_emotion_lookup[[cult1]][[emo1]]) {
      for (cult2 in unique(data$culture)) {
        for (emo2 in EMOTIONS) {
          if (culture_emotion_lookup[[cult2]][[emo2]]) {
            a <- get_cor_vector('culture', cult1, emo1)
            b <- get_cor_vector('culture', cult2, emo2)
            culture_results <- rbind(culture_results, data.frame(
              correlation = cor(a, b),
              emotion1 = emo1,
              emotion2 = emo2,
              group1 = cult1,
              group2 = cult2,
              level = 'culture'
            ))

          }
        }
      }
    }
  }
  print(paste('Finished emotion', emo1))
}
saveRDS(culture_results, "../../results/correlation_analysis/culture_results_with_global.RDS")

############
# Speaker
############
# Takes a while
full_mat <- NULL
first <- TRUE
for (RC in paste0('RC', 1:7)) {
  RC_mat <- params[, stringr::str_detect(names(params), paste0('^r_speaker__mu.+?', RC))]
  colnames(RC_mat) <- stringr::str_replace(stringr::str_remove_all(stringr::str_extract(colnames(RC_mat), 'r_.+?,'), ','), '\\[', '-')

  if (!first) {
    stopifnot(all(colnames(RC_mat) == colnames(full_mat)))
  } else {
    first <- F
  }
  full_mat <- rbind(full_mat, as.matrix(RC_mat))
}

if (ADD_GLOBAL_MAPPING) {
  for (emo in EMOTIONS) {
    col_name_array <- colnames(full_mat)[(stringr::str_detect(colnames(full_mat), emo))]
    estimates <- c()
    for (RC in paste0('RC', 1:7)) {
      estimates <- c(estimates, params[[paste0('b_mu', emo, '_', RC)]])
    }
    for (col_name in col_name_array) {
      full_mat[, col_name] <- full_mat[, col_name] + estimates
    }
  }
}

all_speaker_correlations <- cor(full_mat)
speaker_results <- reshape2::melt(all_speaker_correlations)
names(speaker_results)[3] <- 'correlation'
speaker_results$emotion1 <- stringr::str_extract(speaker_results$Var1, paste0(EMOTIONS, collapse = '|'))
speaker_results$emotion2 <- stringr::str_extract(speaker_results$Var2, paste0(EMOTIONS, collapse = '|'))
speaker_results$group1 <- stringr::str_split_fixed(speaker_results$Var1, '-', 2)[, 2]
speaker_results$group2 <- stringr::str_split_fixed(speaker_results$Var2, '-', 2)[, 2]
speaker_results$level <- 'speaker'
speaker_results$key1 <- paste0(speaker_results$group1, '_', speaker_results$emotion1)
speaker_results$key2 <- paste0(speaker_results$group2, '_', speaker_results$emotion2)

speaker_summary <- data %>%
  group_by(speaker, emotion) %>%
  summarise(key = paste0(speaker[1], '_', emotion[1]))

# Make sure we only include correlations between speaker, emotion pairs that exist in the data.
# The model will also create an estimate for speaker, emotion pairs that do not exist, e.g. if one speaker only produces
# anger, the estimates for the other emotions usually will be low (since they were never shown) but since we add the
# global coefficient as well this would bias our results.
row_idx <- speaker_results$key1 %in% speaker_summary$key & speaker_results$key2 %in% speaker_summary$key

# Make sure result exist for every speaker
saveRDS(speaker_results[row_idx,], "../../results/correlation_analysis/speaker_results_with_global.RDS")

############
# Sex
############
sex_results <- NULL
sexes <- c('F', 'M')
for (emo1 in EMOTIONS) {
  for (sex1 in sexes) {
    for (emo2 in EMOTIONS) {
      for (sex2 in sexes) {
        a <- get_cor_vector('sex', sex1, emo1)
        b <- get_cor_vector('sex', sex2, emo2)
        sex_results <- rbind(sex_results, data.frame(
          correlation = cor(a, b),
          emotion1 = emo1,
          emotion2 = emo2,
          group1 = sex1,
          group2 = sex2,
          level = 'sex'
        ))

      }
    }
  }
  print(paste('Finished emotion', emo1))
}
saveRDS(sex_results, "../../results/correlation_analysis/sex_results_with_global.RDS")
