library(dplyr)
library(ggplot2)

source('../../scripts/annotate_data/load_corpora.R')
EMOTIONS <- c("ANG", "DIS", "FER", "HAP", "SAD", "SUR", "NEU")
out_all <- load_corpora(EMOTIONS, 'eGeMAPS', '../../data/csv/', fully_balanced = F)

eGeMAPS_data = cbind(out_all$X, out_all$meta) %>%
  mutate(filename = as.character(filename)) %>%
  arrange(filename)

eGeMAPS_data %>%
  saveRDS('../../data/eGeMAPS_data.RDS')

data_all = readRDS('../../data/data_all.RDS') %>%
  mutate(filename = as.character(filename)) %>%
  arrange(filename)

stopifnot(all(eGeMAPS_data$filename == data_all$filename))

eGeMAPS_data$country = data_all$country
eGeMAPS_data$language = data_all$language


get_factor_solution = function(data, group, value) {
  filtered_data = filter(data, (!!as.symbol(group)) == value)
  n_factor = 7
  relevant_cols = names(data)[1:88]
  fa <- psych::principal(filtered_data[relevant_cols], nfactors = n_factor, rotate = 'varimax')
  factor_df = as.data.frame(predict(fa, data[relevant_cols]))
  names(factor_df) = paste0('RC', 1:n_factor)
  factor_df
}

obtain_max_correlations = function(df1, df2) {
  all_cor = c()
  exclude_cols = c()
  for (ref_col in names(df1)) {
    comp_cors = c()
    for (comp_col in names(df2)) {
      comp_cors = c(comp_cors, cor(df1[[ref_col]], df2[[comp_col]]))
    }
    # Get the absolute correlation
    abs_comp_cors = abs(comp_cors)
    names(abs_comp_cors) = names(df1)
    # Remove already used factors
    abs_comp_cors = abs_comp_cors[!names(abs_comp_cors) %in% exclude_cols]
    all_cor = c(all_cor, max(abs_comp_cors))
    exclude_cols = c(exclude_cols, names(which.max(abs_comp_cors)))
  }
  stopifnot(length(exclude_cols) == length(names(df1)))
  all_cor
}

mean_crossed_correlation = function(data, group, values) {
  factor_list = list()
  for (value in values) {
    factor_list[[value]] = get_factor_solution(data, group, value)
  }
  results = NULL
  for (lab1 in names(factor_list)) {
    for (lab2 in names(factor_list)) {
      #if (lab1 != lab2)
      df1 = factor_list[[lab1]]
      df2 = factor_list[[lab2]]
      results = rbind(results, data.frame(
        lab1 = lab1,
        lab2 = lab2,
        mean_correlation = mean(abs(obtain_max_correlations(df1, df2)))
      ))
    }
  }
  results
}

# Languages
sort(table(eGeMAPS_data$language))

languages = c('English', 'Basque', 'Hindi', 'Telugu')
language_correlation_df = mean_crossed_correlation(eGeMAPS_data, 'language', languages)
saveRDS(language_correlation_df, '../../data/cross_language_correlation_factor.RDS')

# Plot it if you like
language_correlation_df %>%
  ggplot(aes(x = lab1, y = lab2)) +
  geom_tile(aes(fill = mean_correlation)) +
  geom_text(aes(label = round(mean_correlation, 2)), color = 'white') +
  scale_fill_gradient(low = "#858482", high = "#e50400", breaks = c(0, 0.5, 1), limits = c(0, 1)) +
  labs(
    fill = 'Mean absolute correlation',
    x = '',
    y = ''
  ) +
  ggtitle("Factor solution comparing languages",
          paste('Covering', round(100 * (nrow(filter(eGeMAPS_data, language %in% languages)) / nrow(eGeMAPS_data))), '% of the data')
  ) +
  theme_minimal() +
  theme(
    legend.position = 'bottom'
  )


# Countries
sort(table(eGeMAPS_data$country))
countries = c('India', 'United States', 'Canada', 'Algeria')
country_correlation_df = mean_crossed_correlation(eGeMAPS_data, 'country', countries)
saveRDS(country_correlation_df, '../../data/cross_country_correlation_factor.RDS')

# Plot it if you like
country_correlation_df %>%
  mutate(lab1 = stringr::str_replace_all(lab1, 'United States', 'US')) %>%
  mutate(lab2 = stringr::str_replace_all(lab2, 'United States', 'US')) %>%
  ggplot(aes(x = lab1, y = lab2)) +
  geom_tile(aes(fill = mean_correlation)) +
  geom_text(aes(label = round(mean_correlation, 2)), color = 'white') +
  scale_fill_gradient(low = "#858482", high = "#e50400", breaks = c(0, 0.5, 1), limits = c(0, 1)) +
  labs(
    fill = 'Mean absolute correlation',
    x = '',
    y = ''
  ) +
  ggtitle("Factor solution comparing countries",
          paste('Covering', round(100 * (nrow(filter(eGeMAPS_data, country %in% countries)) / nrow(eGeMAPS_data))), '% of the data')
  ) +
  theme_minimal() +
  theme(
    legend.position = 'bottom'
  )
