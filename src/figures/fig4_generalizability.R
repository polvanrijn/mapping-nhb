library(ggplot2)
library(dplyr)

# Plotting settings
TEXT_SIZE <- 6.5
minimal_theme <- theme_bw() +
  theme(
    legend.position = 'none',
    legend.text = element_text(size = TEXT_SIZE),
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    strip.background = element_blank(),
    title = element_text(size = TEXT_SIZE),
    axis.title = element_text(size = TEXT_SIZE),
    axis.text = element_text(size = TEXT_SIZE, color = 'black'),
    strip.text = element_text(face = 'bold', size = TEXT_SIZE),
    panel.border = element_blank(),
    axis.line = element_line(colour = "black")
  )


EMOTIONS <- c("ANG", "DIS", "FER", "HAP", "SAD", "SUR")
COLORS <- c(
  'ANG' = '#e0677c', #
  'DIS' = '#95ccc4', #
  'FER' = '#f9e156', #
  'HAP' = '#efae7c', #
  'SAD' = '#6469aa',
  'SUR' = '#428fcb' #
)

GROUP_LEVEL_COLORS <- c(
  'corpus' = '#d04065',
  'culture' = '#f39419',
  'sex' = '#38a5a5',
  'speaker' = '#61c6f2'
)

all_data <- readRDS('../../data/data_all.RDS')
results_list <- readRDS('../../results/generalization_analysis/big_model_generalization_analysis_with_all_coefficients_and_intercepts.RDS')
all_long_estimates <- do.call('rbind', results_list$percent_values)

normalize_values <- function(sub_df) {
  sub_df$value <- sub_df$value / sum(sub_df$value)
  sub_df
}

no_intercept <- all_long_estimates %>%
  filter(type != 'intercept') %>%
  group_by(iteration, predicted_emotion) %>%
  do(normalize_values(.))

plot_piechart <- function(dat) {
  dat %>%
    mutate(is_global = group_level == 'global') %>%
    group_by(is_global) %>%
    summarise(percentage = sum(mean)) %>%
    ggplot(aes(x = "", y = percentage, fill = is_global)) +
    geom_bar(stat = "identity", width = 0.5, color = 'black') +
    coord_polar("y", start = 0) +
    theme_minimal() +
    labs(x = '', y = '', title = 'percentage\nglobal') +
    theme(
      axis.text = element_blank(),
      panel.grid = element_blank(),
      legend.position = 'none',
      plot.title = element_text(hjust = 0.5, size = 6.5)
    ) +
    scale_fill_manual(values = c('white', '#bfc0bf'))
}
# For testing
# plot_piechart(dat)

plot_list <- function(plotlist, common.legend = F, remove.x.axis.labels = F, widths = 1, heights = 1) {

  for (i in 1:3) {
    p <- plotlist[[i]]
    p <- p + theme(
      axis.title.x = element_blank()
    )
    if (remove.x.axis.labels) {
      p <- p + theme(
        axis.text.x = element_blank(),
        axis.ticks.x = element_blank()
      )
    }
    plotlist[[i]] <- p
  }

  for (i in c(2:3, 5:6)) {
    plotlist[[i]] <- plotlist[[i]] + theme(
      axis.text.y = element_blank(),
      axis.ticks.y = element_blank(),
      axis.title.y = element_blank()
    )
  }
  if (common.legend) {
    ggpubr::ggarrange(plotlist = plotlist, common.legend = T, legend = 'bottom', widths = widths, heights = heights)
  } else {
    cowplot::plot_grid(plotlist = plotlist, widths = widths, heights = heights)
  }
}

plot_contributions <- function(long_df, x_start, x_end, y_start, y_end, colors) {
  # Get values
  intercept_df <- long_df %>%
    group_by(predicted_emotion, group_level, iteration, type) %>%
    summarise(sum = sum(value)) %>%
    group_by(predicted_emotion, group_level, type) %>%
    filter(type == 'intercept') %>%
    summarise(sd = sd(sum), mean = mean(sum))

  summary_df <- long_df %>%
    group_by(predicted_emotion, group_level, iteration) %>%
    summarise(sum = sum(value)) %>%
    group_by(predicted_emotion, group_level) %>%
    summarise(sd = sd(sum), mean = mean(sum))


  (summary_df %>%
    group_by(predicted_emotion) %>%
    summarise(sum(mean)))

  summary_df$group_level <- factor(summary_df$group_level, names(colors))
  levels(summary_df$predicted_emotion) <- c('Neutral', 'Anger', 'Disgust', 'Fear', 'Happiness', 'Sadness', 'Surprise')
  breaks <- 0:4/10
  levels(intercept_df$predicted_emotion) <- c('Neutral', 'Anger', 'Disgust', 'Fear', 'Happiness', 'Sadness', 'Surprise')
  plotlist <- list()
  for (emo in unique(summary_df$predicted_emotion)) {
    dat <- summary_df %>%
      filter(predicted_emotion == emo)
    dat$share_intercept <- filter(intercept_df, predicted_emotion == emo)$mean
    plotlist[[emo]] <-
      ggplot(dat, aes(x = reorder(group_level, -mean), y = mean, fill = group_level)) +
        geom_bar(stat = 'identity') +
        geom_bar(aes(y = share_intercept), fill = 'black', alpha = 0.2, stat = 'identity') +
        geom_errorbar(aes(ymin = mean - sd, ymax = mean + sd)) +
        minimal_theme +
        scale_fill_manual(values = as.character(colors)) +
        theme(
          axis.text.x = element_blank(),
          axis.ticks.x = element_blank(),
          plot.title = element_text(face = 'bold', size = TEXT_SIZE, hjust = .5),
          legend.text = element_text(size = TEXT_SIZE),
          legend.title = element_text(size = TEXT_SIZE),
          legend.key.width = unit(0.5, 'cm'),
          legend.key.height = unit(0.5, 'cm')
        ) +
        labs(
          title = emo,
          x = 'Coefficients and intercepts',
          y = 'Average contribution (%)',
          fill = 'Levels of analysis'
        ) +
        scale_y_continuous(labels = breaks*100, breaks = breaks, limits = c(-0.01, 0.45)) +
        annotation_custom(
          ggplotGrob(
            plot_piechart(dat)
          ),
          xmin = x_start, xmax = x_end, ymin = y_start, ymax = y_end
        )
  }
  plotlist
}


params <- readRDS('../../results/models/params/params_big_model.RDS')
global_mapping_df <- NULL
estimates <- c()
for (emo in EMOTIONS) {
  for (RC in paste0('RC', 1:7)) {
    estimate <- params[[paste0('b_mu', emo, '_', RC)]]
    global_mapping_df <- rbind(global_mapping_df, data.frame(
      estimate = estimate,
      RC = RC,
      emotion = emo
    ))
    estimates <- c(estimates, estimate)
  }
}
global_estimates_mat <- matrix(estimates, ncol = 6)
colnames(global_estimates_mat) <- EMOTIONS

global_mapping <- as.data.frame(cor(global_estimates_mat)) %>%
  mutate(emotion1 = row.names(.)) %>%
  tidyr::gather(emotion2, correlation, ANG:SUR) %>%
  mutate(level = 'global')

convert_list <- as.list(EMOTIONS)
names(convert_list) <- c('Anger', 'Disgust', 'Fear', 'Happiness', 'Sadness', 'Surprise')


all_with_global <- rbind(
  global_mapping,
  readRDS('../../results/correlation_analysis/sex_results_with_global.RDS') %>%
    mutate(level = 'global + sex') %>%
    select(emotion1, emotion2, correlation, level),
  readRDS('../../results/correlation_analysis/culture_results_with_global.RDS') %>%
    mutate(level = 'global + culture') %>%
    select(emotion1, emotion2, correlation, level),
  readRDS('../../results/correlation_analysis/speaker_results_with_global.RDS') %>%
    mutate(level = 'global + speaker') %>%
    select(emotion1, emotion2, correlation, level)
) %>%
  mutate(level = factor(level, levels = c("global", "global + sex", "global + culture", "global + speaker"))) %>%
  mutate(abs_cor = abs(correlation)) %>%
  group_by(emotion1, emotion2, level) %>%
  summarise(mean = mean(abs_cor))

confusion_plot <- ggplot(all_with_global) +
  geom_tile(aes(x = emotion1, y = emotion2, fill = mean), color = 'white') +
  viridis::scale_fill_viridis(option = "A", limits = c(0, 1)) +
  facet_wrap(~level) +
  minimal_theme +
  labs(
    x = '',
    y = '',
    fill = 'Average correlation'
  ) +
  theme(
    legend.position = 'bottom'
  )

full_plot <- ggpubr::ggarrange(
  cowplot::ggdraw(
    plot_list(plot_contributions(all_long_estimates, x_start = 1.5, x_end = 5.5, y_start = 0.2, y_end = 0.5, colors = c(
      'global' = '#bfc0bf',
      'corpus' = '#d04065',
      'culture' = '#f39419',
      'sex' = '#38a5a5',
      'speaker' = '#61c6f2'
    )),
              common.legend = T, remove.x.axis.labels = T, widths = c(1.27, 1, 1), heights = c(1, 1.07))
  ) +
    cowplot::draw_image(paste0("subfigures/icons/corpus_white.png"), scale = 0.04, halign = 0.42, valign = 0.025) +
    cowplot::draw_image(paste0("subfigures/icons/culture_white.png"), scale = 0.04, halign = 0.562, valign = 0.025) +
    cowplot::draw_image(paste0("subfigures/icons/sex_white.png"), scale = 0.04, halign = 0.703, valign = 0.024) +
    cowplot::draw_image(paste0("subfigures/icons/speaker_white.png"), scale = 0.04, halign = 0.811, valign = 0.026),
  confusion_plot + theme(
  legend.key.height = unit(0.2, 'cm'),
  axis.text.x = element_text(angle = 90, hjust = 1),
  legend.margin = margin(0, 0, 0, 0),
  legend.box.margin = margin(0, 0, 0, 0),
  legend.title = element_text(margin = margin(-10)),
  axis.ticks = element_blank(),
  axis.line = element_blank(),
  plot.margin = unit(c(0.2, 0, 0.8, 0), "cm")
  ),
  widths = c(1.5, 1),
  ncol = 2,
  labels = c("a", "b"),
  font.label = list(size = 8, family = 'Whitney Semibold')
)

ggsave(plot = full_plot, '../../docs/figures/fig4_generalizability.pdf', device = cairo_pdf, width = 175, height = 100, unit = 'mm', dpi = 600)
