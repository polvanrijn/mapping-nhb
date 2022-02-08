library(brms)
library(ggplot2)
library(dplyr)

null_model <- readRDS('../../results/models/null_model.RDS')
base_model <- readRDS('../../results/models/base_model.RDS')
culture_model <- readRDS('../../results/models/culture_model.RDS')
language_model <- readRDS('../../results/models/language_model.RDS')
country_model <- readRDS('../../results/models/country_model.RDS')
big_model <- readRDS('../../results/models/big_model.RDS')
corpus_model <- readRDS('../../results/models/corpus_model.RDS')

waic_compare <- function(model_list, model_names) {
  eval_str <- "loo_compare("
  for (i in 1:length(model_list)) {
    eval_str <- paste0(eval_str, 'model_list[[', i, ']], ')
  }
  eval_str <- paste0(eval_str, "model_names = c('", paste(model_names, collapse = "', '"), "'), criterion = 'waic')")
  eval(parse(text = eval_str))
}

sort_waic_df <- function(waic_df) {
  waic_df %>%
    data.frame() %>%
    tibble::rownames_to_column("model_name") %>%
    mutate(model_name = forcats::fct_reorder(model_name, waic, .desc = T))
}

waic_plot_data <- waic_compare(list(
  null_model,
  base_model,
  corpus_model,
  culture_model,
  big_model
), c('null', 'base', 'corpus', 'in-group', 'big'))[, 7:8]

conf_mats <- list(
  'Base' = readRDS('../../results/confusion_matrices/base_model_conf_mat.RDS'),
  'In-group' = readRDS('../../results/confusion_matrices/culture_model_conf_mat.RDS'),
  'Big' = readRDS('../../results/confusion_matrices/big_model_conf_mat.RDS')
)

conf_mat_long <- data.frame()
for (title in names(conf_mats)) {
  conf_mat <- conf_mats[[title]]
  UAR <- round(mean(conf_mat$byClass[, 1]) * 100, 1)
  rows <- reshape2::melt(conf_mat$table / apply(conf_mat$table, 2, sum))
  rows$title <- paste0(title, '\nUAR: ', UAR, '%')
  conf_mat_long <- rbind(conf_mat_long, rows)
}

# Optionally to save memory
# remove(model_null)
# remove(model_base)
# remove(model_big)

# Plot settings
TEXT_SIZE <- 6.5
minimal_theme <- theme_bw() +
  theme(
    legend.position = 'none',
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

add_img <- function(name, x, y, scale = 0.04) {
  cowplot::draw_image(paste0("subfigures/icons/", name, ".png"), scale = scale, halign = x, valign = y)
}

no_y <- theme(
  axis.text.y = element_blank(),
  axis.ticks.y = element_blank()
)

heatmap_colors <- c(
  '#f1de90',
  '#f8c366',
  '#fda73e',
  '#fc8a24',
  '#fc6a0b',
  '#f04f09',
  '#d8382e',
  '#c62833',
  '#AF1C43',
  '#8A1739',
  '#701547',
  '#4C0D3E'
)

icon_y <- 1.2
SE_to_CI <- function(x) x * 1.96

specificity_plot <- ggpubr::ggarrange(
  ggpubr::ggarrange(
    sort_waic_df(waic_plot_data) %>%
      ggplot() +
      geom_pointrange(aes(
        x = waic,
        y = 0,
        xmin = waic - SE_to_CI(se_waic),
        xmax = waic + SE_to_CI(se_waic)
      ), size = 0.2) +
      geom_text(data=sort_waic_df(waic_plot_data)[4:5,], aes(x = waic, y = 0.2, label=model_name), size=2.5) +
      labs(
        x = 'WAIC',
        y = ''
      ) +
      minimal_theme +
      no_y +
      geom_rect(xmin = 133000, xmax = 140500, ymin = -0.05, ymax = 0.05, color = "black", fill = NA) +
      ylim(-0.3, 0.3) +
      scale_x_reverse() +
      xlim(90000, 185000) +
      annotation_custom(
        ggplotGrob(
          cowplot::ggdraw() +
            add_img('big', x = -.05, y = icon_y, scale = 0.3) +
            add_img('country-language', x = .50, y = icon_y, scale = 0.3) +
            add_img('corpus', x = .38, y = icon_y, scale = 0.3)
        ),
        xmin = 90000, xmax = 185000, ymin = -0.4, ymax = 0.2
      ),
    sort_waic_df(waic_compare(list(
      culture_model,
      language_model,
      country_model
    ), c('interaction', 'language', 'country'))[, 7:8]) %>%
      ggplot() +
      geom_pointrange(aes(
        x = waic,
        y = 0,
        xmin = waic - SE_to_CI(se_waic),
        xmax = waic + SE_to_CI(se_waic)
      ), size = 0.2) +
      labs(
        x = 'WAIC',
        y = ''
      ) +
      minimal_theme +
      no_y +
      xlim(133000, 140500) +
      scale_x_continuous(n.breaks = 2) +
      ylim(-0.3, 0.3) +
      theme(
        panel.border = element_rect(colour = "black", size = 1, fill = NA),
        #panel.background = element_blank(),
        plot.background = element_blank(),
        axis.line = element_blank()
      ) +
      annotation_custom(
        ggplotGrob(
          cowplot::ggdraw() +
            add_img('culture', x = .3, y = icon_y, scale = 0.25) +
            add_img('country', x = .73, y = icon_y, scale = 0.25) +
            add_img('language', x = .92, y = icon_y, scale = 0.25)
        ),
        xmin = 133000, xmax = 140500, ymin = -0.4, ymax = 0.2
      ),
    ncol = 2,
    widths = c(3, 1),
    labels = c("a", "b"),
    font.label = list(size = 8, family = 'Whitney Semibold')
  ),
  ggpubr::ggarrange(
    cowplot::ggdraw() +
      cowplot::draw_image(magick::image_read_pdf("subfigures/language_tree.pdf", density = 600)),
    cowplot::ggdraw() +
      cowplot::draw_image(magick::image_read_pdf("subfigures/country_tree.pdf", density = 600)),
    ncol=2,
    labels = c("c", "d"),
    font.label = list(size = 8, family = 'Whitney Semibold')
  ),
  conf_mat_long %>%
    mutate(v_bin = cut_interval(value, length(heatmap_colors))) %>%
    mutate(title = factor(title, unique(conf_mat_long$title))) %>%
    ggplot() +
    geom_tile(aes(x = Prediction, y = Reference, fill = v_bin), color='white') +
    scale_fill_manual(values = heatmap_colors) +
    labs(
      fill = 'Normalized frequency'
    ) +
    minimal_theme +
    theme(
      axis.ticks = element_blank(),
      axis.line = element_blank(),
      legend.position = 'bottom',
      axis.text.x = element_text(angle = 90),
      legend.text = element_blank(),
      legend.key.width = unit(0.45, 'cm'),
      legend.key.height = unit(0.2, 'cm'),
      legend.spacing.x = unit(0, 'cm'),
      plot.margin = unit(c(0, 2, 0, 2), "cm"),
      legend.margin = margin(0, 0, 0, 0),
      legend.box.margin = margin(0, 0, 0, 0)
    ) +
    guides(fill = guide_legend(nrow = 1)) +
    facet_grid(~ title),
  nrow = 3,
  heights = c(1, 2, 2.3),
  labels = c("", "", "e"),
  font.label = list(size = 8, family = 'Whitney Semibold')
)
ggsave(plot=specificity_plot,'../../docs/figures/fig3_specificity.pdf', device = cairo_pdf, width = 142, height = 120, unit = 'mm')
