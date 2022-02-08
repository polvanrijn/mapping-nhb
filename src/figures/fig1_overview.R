library(dplyr)
library(brms)
library(ggplot2)

# Plotting Settings
TEXT_SIZE <- 6.5
minimal_theme <- theme_bw() +
  theme(
    legend.position = 'bottom',
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    strip.background = element_blank(),
    title = element_text(size = TEXT_SIZE, color = 'black'),
    plot.title = element_text(size = TEXT_SIZE, color = 'black'),
    axis.title = element_text(size = TEXT_SIZE, color = 'black'),
    axis.text = element_text(size = TEXT_SIZE, color = 'black'),
    strip.text = element_text(size = TEXT_SIZE),
    panel.border = element_blank(),
    axis.line = element_line(colour = "black"),
    legend.title = element_text(size = TEXT_SIZE, color = 'black'),
    legend.text = element_text(size = TEXT_SIZE, color = 'black'),
    legend.key.height = unit(0.2, 'cm'),
    legend.margin = margin(0, 0, 0, 0),
    legend.box.margin = margin(0, 0, 0, 0)
  )

factor.df.wide <- readRDS('../../data/factor_df_wide.RDS')
eGeMAPS_annotation <- read.csv('../annotate_data/eGeMAPS_annotation.csv')
country_correlation_df <- readRDS('../../data/cross_country_correlation_factor.RDS')
language_correlation_df <- readRDS('../../data/cross_language_correlation_factor.RDS')
eGeMAPS_data <- readRDS('../../data/eGeMAPS_data.RDS')
languages <- c('English', 'Basque', 'Hindi', 'Telugu')
countries <- c('India', 'United States', 'Canada', 'Algeria')
n_factor <- 7

# Reload the factor df
factor.df <- reshape2::melt(factor.df.wide)

# Name the columns
names(factor.df) <- c('factor', 'loading')

# Annotate with eGeMAPS groups
factor.df$feature_idx <- 1:88
for (col in c('feature', 'group', 'subgroup')) {
  vals <- eGeMAPS_annotation[[col]]
  factor.df[[col]] <- vals[factor.df$feature_idx]
}


# Create mapping

se <- function(x) sd(x) / sqrt(length(x))
CI <- function(x) se(x) * 1.96
BREAKS <- 1:7

process_posteriors <- function(posterior_list) {
  result <- data.frame()
  first <- TRUE
  for (mapping_name in names(posterior_list)) {
    l <- posterior_list[[mapping_name]]
    if (first) {
      all_data <- l
      first <- FALSE
    } else {
      all_data <- all_data + l
    }
    out <- do.call('rbind', apply(l, 2, function(x) {
      mu <- mean(x)
      x_CI <- CI(x)
      data.frame(
        mu = mu,
        l_95 = mu - x_CI,
        u_95 = mu + x_CI
      )
    }))
    out$feature <- BREAKS
    out$level <- mapping_name
    result <- rbind(result, out)
  }

  out <- do.call('rbind', apply(all_data, 2, function(x) {
    mu <- mean(x)
    x_CI <- CI(x)
    data.frame(
      mu = mu,
      l_95 = mu - x_CI,
      u_95 = mu + x_CI
    )
  }))
  out$feature <- BREAKS
  out$level <- 'combined'
  result <- rbind(result, out)
  result
}

data <- readRDS('../../data/data_all.RDS')
params <- readRDS('../../results/models/params/params_big_model.RDS')

# Rename culture
data$culture <- stringr::str_replace_all(paste0(data$country, '_', data$language), ' ', '.')
names(params) <- stringr::str_replace_all(names(params), 'country:language', 'culture')

factor_names <- c('voice quality', 'loudness', 'pitch & formants', 'rhythm & tempo', 'shimmer', 'pitch variation', 'MFCC 3')

BASIC_EMOTIONS <- c("ANG", "DIS", "FER", "HAP", "SAD", "SUR")
CURRENT_EMOTION <- 'ANG'
corpus_name <- 'VEN'
sex_name <- 'M'
culture_name <- 'Kenya_English'
speaker_name <- 'VEN_CK'
predictions <- c()

posterior_list <- list(
  'global_mapping' = posterior_samples(params, paste0('^b_mu', CURRENT_EMOTION, '_RC')),
  'culture' = posterior_samples(params, paste0('^r_culture__mu', CURRENT_EMOTION, '\\[', culture_name, ',RC')),
  'sex' = posterior_samples(params, paste0('^r_sex__mu', CURRENT_EMOTION, '\\[', sex_name, ',RC')),
  'speaker' = posterior_samples(params, paste0('^r_speaker__mu', CURRENT_EMOTION, '\\[', speaker_name, ',RC'))
)

posterior_df <- process_posteriors(posterior_list)
posterior_df$level <- factor(posterior_df$level, c(names(posterior_list), 'combined'))
COLORS <- c(
  'global_mapping' = '#bfc0bf',
  'culture' = '#f39419',
  'sex' = '#38a5a5',
  'speaker' = '#61c6f2',
  'combined' = '#000000'
)

example_data <- as.numeric((data %>%
  filter(corpus == corpus_name, speaker == speaker_name, emotion == CURRENT_EMOTION) %>%
  head(1))[paste0('RC', BREAKS)])

for (emo in  BASIC_EMOTIONS) {
  # Get the sum
  acc_coeffs <- sum((process_posteriors(list(
    'global_mapping' = posterior_samples(params, paste0('^b_mu', emo, '_RC')),
    'culture' = posterior_samples(params, paste0('^r_culture__mu', emo, '\\[', culture_name, ',RC')),
    'sex' = posterior_samples(params, paste0('^r_sex__mu', emo, '\\[', sex_name, ',RC')),
    'speaker' = posterior_samples(params, paste0('^r_speaker__mu', emo, '\\[', speaker_name, ',RC'))
  )) %>%
    filter(level == 'combined')
                   )$mu * example_data)

  intercepts <- c(
    mean(params[[paste0('b_mu', emo, '_Intercept')]]),
    mean(params[[paste0('r_corpus__mu', emo, '[', corpus_name, ',Intercept]')]]),
    mean(params[[paste0('r_culture__mu', emo, '[', culture_name, ',Intercept]')]]),
    mean(params[[paste0('r_sex__mu', emo, '[', sex_name, ',Intercept]')]]),
    mean(params[[paste0('r_speaker__mu', emo, '[', speaker_name, ',Intercept]')]])
  )
  predictions <- c(predictions, acc_coeffs + sum(intercepts))
}


global_mapping <- posterior_df %>%
  mutate(level = forcats::fct_recode(level, "Global\nAnger" = "global_mapping", "Kenyan\nAnger" = "culture", "Male\nAnger" = "sex", "Speaker CK\nAnger" = "speaker", " " = "combined")) %>%
  filter(level == ' ')

multiplied_values <- (process_posteriors(list(
  'global_mapping' = posterior_samples(params, paste0('^b_mu', CURRENT_EMOTION, '_RC')),
  'culture' = posterior_samples(params, paste0('^r_culture__mu', CURRENT_EMOTION, '\\[', culture_name, ',RC')),
  'sex' = posterior_samples(params, paste0('^r_sex__mu', CURRENT_EMOTION, '\\[', sex_name, ',RC')),
  'speaker' = posterior_samples(params, paste0('^r_speaker__mu', CURRENT_EMOTION, '\\[', speaker_name, ',RC'))
)) %>%
  filter(level == 'combined')
)$mu * example_data

estimates_after_softmax <- round(rethinking::softmax(c(0, predictions)), 2)

plot_it <- function() {
  # Simple  loading plot
  loading_plot <- factor.df %>%
    mutate(abs_loading = abs(loading)) %>%
    mutate(abs_loading = ifelse(abs_loading < 0.45, 0, abs_loading)) %>%
    mutate(factor = as.numeric(factor)) %>%
    mutate(subgroup = forcats::fct_recode(subgroup, "harmonic diff." = "harmonic difference", "Hammar. index" = "Hammarberg index")) %>%
    group_by(factor, subgroup) %>%
    summarise(mean_abs_loading = mean(abs_loading), median_abs_loading = median(abs_loading)) %>%
    ggplot(aes(x = factor, y = subgroup, fill = median_abs_loading)) +
    geom_tile(color = 'gray') +
    viridis::scale_fill_viridis(option = "D", limits = c(0, 1), breaks = c(0, 1)) +
    scale_x_reverse(
      breaks = 1:n_factor,
      labels = factor_names,
      name = 'Factor',
      sec.axis = sec_axis(trans = ~., labels = 1:7, breaks = 1:7),
      expand = c(0, 0)
    ) +
    scale_y_discrete(labels = function(x) stringr::str_wrap(x, width = 15)) +
    labs(
      y = ''
    ) +
    coord_flip() +
    minimal_theme +
    theme(
      axis.title.y = element_blank(),
      #axis.text.y.right = element_text(margin = margin(0, -3, 0, -3)),
      axis.line = element_blank(),
      panel.grid = element_blank(),
      panel.border = element_blank(),
      legend.position = 'none',
      axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5),
      legend.margin = margin(0, 0, 0, 0, unit = 'cm'),
      axis.ticks = element_blank(),
      plot.margin = unit(c(0.2, 0, 0, 0.2), "cm")
    )

  plot_cross_corr <- function(df, title) {
    df %>%
      filter(lab1 != lab2) %>%
      rowwise() %>%
      mutate(set = paste(sort(c(lab1, lab2)), collapse = 'X')) %>%
      group_by(set) %>%
      summarise(lab1 = lab1[1], lab2 = lab2[1], mean_correlation = mean(mean_correlation)) %>%
      ggplot(aes(x = lab1, y = lab2)) +
      geom_point(aes(color = mean_correlation)) +
      geom_tile(aes(fill = mean_correlation), color = 'white') +
      viridis::scale_fill_viridis(option = "C", limits = c(0, 1), breaks = c(0, 1)) +
      viridis::scale_color_viridis(option = "D", limits = c(0, 1), breaks = c(0, 1)) +
      labs(
        x = '',
        y = '',
        color = 'MAL',  # Median absolute loading
        fill = 'MAC'  # Mean absolute correlation
      ) +
      # scale_x_discrete(labels = function(x) stringr::str_wrap(x, width = 12)) +
      # scale_y_discrete(labels = function(x) stringr::str_wrap(x, width = 12)) +
      ggtitle(title) +
      minimal_theme +
      theme(
        plot.margin = unit(c(0, 0, 0, 0), "cm"),
        axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5),
        # plot.title.position = "plot",
        legend.position = 'none',
        legend.key.width = unit(0.4, 'cm'),
        legend.key.height = unit(0.25, 'cm'),
        legend.box.margin = margin(0, 0, 0, 0.4, unit = 'cm')
      )
  }

  cross_language_cor_plot <- plot_cross_corr(
    language_correlation_df %>%
      mutate(lab1 = forcats::fct_recode(lab1, TE = "Telugu", HI = "Hindi", EU = "Basque", EN = "English")) %>%
      mutate(lab2 = forcats::fct_recode(lab2, TE = "Telugu", HI = "Hindi", EU = "Basque", EN = "English")),
    paste0("Largest languages", '\n', '(', round(100 * (nrow(filter(eGeMAPS_data, language %in% languages)) / nrow(eGeMAPS_data))), '% of all data)')
  )

  cross_country_cor_plot <- plot_cross_corr(
    country_correlation_df %>%
      mutate(lab1 = forcats::fct_recode(lab1, US = "United States", CA = "Canada", IN = "India", DZ = "Algeria")) %>%
      mutate(lab2 = forcats::fct_recode(lab2, US = "United States", CA = "Canada", IN = "India", DZ = "Algeria")),
    paste0("Largest countries", '\n', '(', round(100 * (nrow(filter(eGeMAPS_data, country %in% countries)) / nrow(eGeMAPS_data))), '% of all data)')
  )

  factor_subplots <- ggpubr::ggarrange(
    loading_plot
  )
  schematics <- ggpubr::ggarrange(
    cowplot::ggdraw() +
      cowplot::draw_image(magick::image_read_pdf("subfigures/mapping.pdf", density = 600)) +
      theme(plot.margin = unit(c(0, 0.3, 0, 0.3), "cm")),
    cowplot::ggdraw() +
      cowplot::draw_image(magick::image_read_pdf("subfigures/basic_emotions.pdf", density = 600)) +
      theme(plot.margin = unit(c(0, 0.3, 0, 0.3), "cm")),
    nrow = 2,
    labels = c("a", "c"),
    font.label = list(size = 8, family = 'Whitney Semibold')
  )
  upper_plot <- ggpubr::ggarrange(
    schematics,
    factor_subplots,
    ncol = 2,
    widths = c(1, 2),
    labels = c("", "b"),
    font.label = list(size = 8, family = 'Whitney Semibold')
  )

  lower_plot <- ggpubr::ggarrange(
    cowplot::ggdraw(posterior_df %>%
                      mutate(level = forcats::fct_recode(level, "Global\nAnger" = "global_mapping", "Kenyan\nAnger" = "culture", "Male\nAnger" = "sex", "Speaker CK\nAnger" = "speaker", " " = "combined")) %>%
                      ggplot(aes(x = feature, y = mu)) +
                      geom_hline(yintercept = 0, color = 'grey') +
                      geom_line(aes(color = level)) +
                      geom_point(aes(color = level)) +
                      geom_ribbon(aes(x = feature, ymin = u_95, ymax = l_95, fill = level), alpha = 0.6) +
                      coord_flip() +
                      facet_grid(. ~ level) +
                      minimal_theme +
                      labs(
                        x = '',
                        y = ''
                      ) +
                      scale_fill_manual(values = as.character(COLORS)) +
                      scale_color_manual(values = as.character(COLORS)) +
                      scale_x_reverse(
                        labels = stringr::str_wrap(factor_names, width = 10),
                        breaks = BREAKS
                      ) +
                      theme(
                        axis.line.x = element_blank(),
                        axis.ticks.x = element_blank(),
                        axis.text.x = element_blank(),
                        legend.position = 'none',
                        plot.margin = margin(0, 0, 0, 0),
                      ) +
                      ylim(-2, 8)
    ) +
      cowplot::draw_text('+', x = 0.29) +
      cowplot::draw_text('+', x = 0.47) +
      cowplot::draw_text('+', x = 0.63) +
      cowplot::draw_text('=', x = 0.8),
    posterior_df %>%
      mutate(level = forcats::fct_recode(level, "Global\nAnger" = "global_mapping", "Kenyan\nAnger" = "culture", "Male\nAnger" = "sex", "Speaker CK\nAnger" = "speaker", " " = "combined")) %>%
      filter(level == ' ') %>%
      ggplot(aes(x = feature, y = mu)) +
      geom_hline(yintercept = 0, color = 'grey') +
      geom_line(color = 'black') +
      geom_point(color = 'black') +
      geom_ribbon(aes(x = feature, ymin = u_95, ymax = l_95), alpha = 0.6) +
      geom_text(data = data.frame(feature = BREAKS, mu = global_mapping$mu - 14, label = paste(round(example_data, 1), '×')), aes(label = label), size = 2) +
      geom_text(data = data.frame(feature = BREAKS, mu = global_mapping$mu + 14, label = paste('=', round(multiplied_values, 1))), aes(label = label), size = 2) +
      geom_text(data = data.frame(
        label = c('1 Multiply\nthe mapping', paste0('2 Sum the\nvalues up', '\n= ', round(sum(multiplied_values), 1)), paste0('3 Add\nintercepts\n= ', round(predictions[1], 1))),
        feature = c(1.2, 4, 6),
        mu = c(35, 29, 33)
      ), aes(label = label), size = 2, hjust = 0, lineheight = .9) +
      coord_flip() +
      facet_grid(. ~ level) +
      minimal_theme +
      labs(
        x = '',
        y = ''
      ) +
      scale_x_reverse(
        labels = stringr::str_wrap(factor_names, width = 10),
        breaks = BREAKS
      ) +
      theme(
        axis.line.x = element_blank(),
        axis.ticks.x = element_blank(),
        axis.text.x = element_blank(),
        legend.position = 'none',
        plot.margin = margin(0, 0, 0, 0),
      ) +
      ylim(-25, 70),
    ncol = 2,
    labels = c("d", "e"),
    font.label = list(size = 8, family = 'Whitney Semibold'),
    widths = c(1.9, 1)
  )
  full_plot <- ggpubr::ggarrange(
    ggpubr::ggarrange(upper_plot, lower_plot, nrow = 2),
    ggpubr::ggarrange(
      ggpubr::ggarrange(
        cross_language_cor_plot,
        cross_country_cor_plot,
        nrow = 2,
        common.legend = T,
        legend = 'right'
      ) +
        theme(plot.margin = unit(c(0.2, .5, 0, 0.7), "cm")),
      cowplot::ggdraw(
        ggplot() +
          minimal_theme +
          geom_text(aes(x = 5, y = 10, label = paste0('[', paste(c('NEU', BASIC_EMOTIONS), collapse = ', '), ']')), size = 2.2) +
          geom_text(aes(x = 5, y = 9.3, label = paste0('[', paste(round(c(0, predictions), 2), collapse = ', '), ']')), size = 2.2) +
          geom_segment(aes(x = 5, y = 7.7, yend = 8.7, xend = 5), arrow = arrow(length = unit(0.10, "cm"), ends = "first", type = "closed")) +
          geom_text(aes(x = 5.5, y = 8.4, label = 'softmax'), size = 2.2, hjust = 0) +

          geom_text(aes(x = 5, y = 7, label = paste0('[', paste(estimates_after_softmax, collapse = ', '), ']')), size = 2.2) +
          geom_segment(aes(x = 3.7, y = 5.1, yend = 6.1, xend = 3.7), arrow = arrow(length = unit(0.10, "cm"), ends = "first", type = "closed")) +
          geom_text(aes(x = 4.2, y = 5.8, label = 'argmax'), size = 2.2, hjust = 0) +

          ylim(3, 10) +
          xlim(0, 10) +
          theme(
            axis.text = element_blank(),
            axis.line = element_blank(),
            axis.ticks = element_blank()
          ) +
          labs(
            y = '',
            x = ''
          )
      ) +
        cowplot::draw_image(magick::image_read_pdf("subfigures/anger.pdf", density = 600), x = 0.31, y = -0.24, width = 0.3),
      nrow = 2,
      heights = c(2, 1),
      labels = c("", "f"),
      font.label = list(size = 8, family = 'Whitney Semibold')
    ),
    ncol = 2,
    widths = c(2.5, 1)
  )
  ggsave(plot = full_plot, '../../docs/figures/fig1_overview.pdf', device = cairo_pdf, width = 175, height = 90, unit = 'mm')
}
plot_it()
