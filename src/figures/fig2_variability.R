library(brms)
library(ggplot2)
library(dplyr)
library(ggridges)

#####################
# Helper functions
#####################

se <- function(x) sd(x) / sqrt(length(x))

CI <- function(x) se(x) * 1.96

std <- function(x) sd(x) / sqrt(length(x))

.tr <- function(X) { return(sum(diag(X))) }

.invcalc <- function(X, W, k) {
  sWX <- sqrt(W) %*% X
  res.qrs <- qr.solve(sWX, diag(k))
  return(tcrossprod(res.qrs))
}

# Compute CI and mean for posteriors
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

###############################################################################
# Computation inspired from: https://mvuorre.github.io/posts/2016-09-29-bayesian-meta-analysis/
# Compute h2
###############################################################################
compute_h2 <- function(emotion_str, feature) {
  # Only include corpora with the emotion
  corpora <- filter(corpus_emotion, emotion == emotion_str)$corpus

  coefs <- c()
  dat <- NULL
  for (corpus_name in corpora) {
    # Get the global coefficient estimates
    global_col_name <- paste0('b_mu', emotion_str, '_', feature)
    global_est <- params[[global_col_name]]
    # Get the coefficient estimates for a specific corpus
    local_col_name <- paste0('r_corpus__mu', emotion_str, '[', corpus_name, ',', feature, ']')
    local_est <- params[[local_col_name]]
    # Combine them
    comb_est <- global_est + local_est
    yi <- mean(comb_est)

    dat <- rbind(dat, data.frame(
      yi = yi,
      sei = as.numeric(quantile(comb_est, prob = 0.95) - mean(comb_est))
    ))

    coefs <- c(coefs, mean_params[local_col_name])
  }

  col_name <- paste0('sd_corpus__mu', emotion_str, '_', feature)

  tau <- mean_params[[col_name]]
  tau2 <- tau^2

  p <- 1
  k <- nrow(dat)
  vi <- dat$sei^2
  wi <- 1 / vi
  # Empty matrix with diagonal
  W.FE <- diag(wi, nrow = k, ncol = k)

  # Study intercepts
  X <- cbind(coefs = as.numeric(coefs))

  stXWX <- .invcalc(X = X, W = W.FE, k = k)
  P <- W.FE - W.FE %*% X %*% stXWX %*% crossprod(X, W.FE)
  vt <- (k - p) / .tr(P)

  Y <- as.matrix(dat$yi)
  QE <- max(0, c(crossprod(Y, P) %*% Y)) # Q statistic
  QEp <- pchisq(QE, df = k - p, lower.tail = FALSE)


  I2 <- 100 * mean(tau2) / (vt + mean(tau2))
  H2 <- mean(tau2) / vt + 1
  data.frame(
    emotion = emotion_str,
    feature = feature,
    I2 = I2,
    H2 = H2,
    QE = QE,
    QEp = QEp
  )
}

###########################
# Process data
###########################

corpus_model <- readRDS('../../results/models/corpus_model.RDS')
BASIC_EMOTIONS <- list("ANG", "DIS", "FER", "HAP", "SAD", "SUR")
params <- brms::posterior_samples(corpus_model)
mean_params <- apply(params, 2, mean)

corpus_emotion <- corpus_model$data %>%
  filter(emotion != "NEU") %>%
  group_by(corpus, emotion) %>%
  summarise() %>%
  data.frame()

# Compute h2 for each feature and each emotion
out <- list()
idx <- 0
for (emotion in BASIC_EMOTIONS) {
  for (feature in paste0('RC', 1:7)) {
    idx <- idx + 1
    out[[idx]] <- compute_h2(emotion, feature)
  }
}

h2_table <- do.call('rbind', out) %>%
  mutate(QEp_sign = ifelse(QEp <= 0.001, '***', ifelse(QEp <= 0.01, '**', ifelse(QEp <= 0.05, '*', '')))) %>%
  arrange(desc(feature)) %>%
  arrange(emotion, feature)

results <- NULL
draw_results <- NULL
for (corpus_name in unique(corpus_model$data$corpus)) {
  # Filter out corpora that do not contain certain the emotion
  available_emotions <- as.character(filter(corpus_emotion, corpus == corpus_name)$emotion)
  for (emotion in available_emotions) {
    for (feature in paste0('RC', 1:7)) {

      global_col_name <- paste0('b_mu', emotion, '_', feature)
      global_est <- params[[global_col_name]]
      mean_global <- mean(global_est)


      local_col_name <- paste0('r_corpus__mu', emotion, '[', corpus_name, ',', feature, ']')
      local_est <- params[[local_col_name]]
      comb_est <- global_est + local_est
      results <- rbind(results, data.frame(
        emotion = emotion,
        feature = feature,
        corpus = corpus_name,
        estimate = mean_global + mean(local_est),
        se = std(comb_est),
        CI = quantile(comb_est, prob = 0.95) - mean(comb_est)
      ))
      # Separately store the results for anger and loudness
      if (emotion == 'ANG' & feature == 'RC2') {
        draw_results <- rbind(draw_results, data.frame(
          emotion = emotion,
          feature = feature,
          corpus = corpus_name,
          draws = comb_est
        ))
      }
    }
  }
}

# Compute the averages
summary_df <- NULL
for (emotion in BASIC_EMOTIONS) {
  for (feature in paste0('RC', 1:7)) {
    global_col_name <- paste0('b_mu', emotion, '_', feature)
    global_est <- params[[global_col_name]]

    summary_df <- rbind(summary_df, data.frame(
      emotion = emotion,
      feature = feature,
      estimate = mean(global_est),
      se = std(global_est),
      CI = quantile(global_est, prob = 0.95) - mean(global_est)
    ))
  }
}


summary_df <- summary_df %>%
  arrange(emotion, feature)

# Make sure h2_table and summary_df are properly aligned
stopifnot(all(h2_table$feature == summary_df$feature))
stopifnot(all(h2_table$emotion == summary_df$emotion))
summary_df$I2 <- round(h2_table$I2)

# Rename the columns
emotion_names <- c(ANG = 'Anger', HAP = 'Happiness', SAD = 'Sadness', FER = 'Fear', DIS = 'Disgust', SUR = 'Surprise')
feature_names <- c(RC1 = "voice\nquality", RC2 = "loudness", RC3 = "pitch &\nformants", RC4 = "rhythm &\ntempo", RC5 = "shimmer", RC6 = "pitch\nvariation", RC7 = "MFCC 3")
summary_df <- summary_df %>%
  mutate(feature_description = recode(feature, !!!feature_names)) %>%
  mutate(emotion_label = recode(emotion, !!!emotion_names)) %>%
  mutate(emotion_label = factor(emotion_label, as.character(emotion_names))) %>%
  mutate(factor_number = as.numeric(stringr::str_remove(feature, 'RC')))
results <- results %>%
  mutate(feature_description = recode(feature, !!!feature_names)) %>%
  mutate(emotion_label = recode(emotion, !!!emotion_names)) %>%
  mutate(emotion_label = factor(emotion_label, as.character(emotion_names))) %>%
  mutate(factor_number = as.numeric(stringr::str_remove(feature, 'RC')))

# Prepare data for zoomed in plot
RC2_ANG <- results %>%
  filter(emotion_label == 'Anger', feature == 'RC2') %>%
  mutate(corpus = forcats::fct_reorder(corpus, estimate, .desc = T))
RC2_ANG_mu <- summary_df %>%
  filter(emotion_label == 'Anger', feature == 'RC2')

# Use same ordering of the corpora
draw_results$corpus <- factor(draw_results$corpus, levels(RC2_ANG$corpus))
results$corpus <- factor(results$corpus, levels(RC2_ANG$corpus))

# Prepare example mapping plot
CURRENT_EMOTION <- 'ANG'
corpus_name <- 'SAV'
posterior_list <- list(
  'global_mapping' = brms::posterior_samples(params, paste0('^b_mu', CURRENT_EMOTION, '_RC')),
  'corpus' = brms::posterior_samples(params, paste0('^r_corpus__mu', CURRENT_EMOTION, '\\[', corpus_name, ',RC'))
)
posterior_df <- process_posteriors(posterior_list)

# Settings for the plot
OUTER_VAL <- 15
BREAKS <- 1:7
COLORS <- c(
  'global_mapping' = '#bfc0bf',
  'corpus' = '#d04065',
  'combined' = '#000000'
)
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

# The individual plots
corpus_example_mapping <- cowplot::ggdraw(
  posterior_df %>%
    mutate(CI = (u_95 - l_95)) %>%
    mutate(level = factor(level, levels = c('global_mapping', 'corpus', 'combined'))) %>%
    mutate(level = forcats::fct_recode(level, "Global\nAnger" = "global_mapping", "Corpus SAV\nAnger" = "corpus", " " = "combined")) %>%
    ggplot(aes(x = feature, y = mu)) +
    geom_hline(yintercept = 0, color = 'grey') +
    geom_line(aes(color = level)) +
    geom_point(aes(color = level, size = 1 / CI)) +
    scale_size_continuous(range = c(1, 3)) +
    geom_ribbon(aes(x = feature, ymin = u_95, ymax = l_95, fill = level), alpha = 0.7) +
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
    labels = paste('RC', BREAKS),
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
  cowplot::draw_text('+', x = 0.37) +
  cowplot::draw_text('=', x = 0.67)

zoomed_in_plot <- ggplot(data = NULL, aes = NULL) +
      geom_vline(data = RC2_ANG_mu, aes(xintercept = estimate)) +
      geom_vline(data = NULL, aes(xintercept = 0), color = 'grey', size = 0.5) +
      geom_density_ridges(aes(x = draws, y = corpus, fill = corpus), draw_results, color = NA) +
      geom_point(data = RC2_ANG, aes(x = estimate, y = corpus)) +
      # plot with .05, .95 CIs
      geom_linerange(data = RC2_ANG, aes(y = corpus, xmin = estimate - CI, xmax = estimate + CI)) +
      theme_bw() +
      theme(
        axis.ticks = element_blank(),
        legend.position = 'none',
        axis.text = element_text(size = TEXT_SIZE, color = 'black'),
        plot.title = element_text(size = TEXT_SIZE, color = 'black'),
        title = element_text(size = TEXT_SIZE, color = 'black'),
        panel.grid = element_blank(),
        panel.border = element_rect(size = 1.4)
      ) +
      scale_fill_viridis_d(option = 'B') +
      labs(
        title = 'Anger, loudness (RC2)',
        y = 'Corpora',
        x = 'Distributions'
      ) +
      xlim(-1, OUTER_VAL)

variability_overview_plot <- ggplot(results, aes(y = estimate, x = factor_number)) +
    geom_hline(yintercept = 0, color = 'grey', size = 0.5) +
    geom_line(data = summary_df, aes(group = 1), color = 'black') +
    geom_ribbon(data = summary_df, aes(group = 1, ymin = estimate - CI, ymax = estimate + CI), alpha = 0.3) +
    geom_point(aes(color = corpus, size = 1 / CI), alpha = .5) +
    geom_text(data = summary_df, aes(y = 12, label = paste(I2, '%')), size = 2.7, color='gray20') +
    scale_x_reverse( # Features of the first axis
      labels = paste('RC', BREAKS),
      breaks = BREAKS,
      # Add a second axis and specify its features
      sec.axis = sec_axis(trans = ~., labels = as.character(feature_names), breaks = BREAKS)
    ) +
    geom_rect(data = data.frame(emotion_label = 'Anger', factor_number = 2, feature = 'RC2', estimate = 0), mapping = aes(xmin = 1.5, xmax = 2.5, ymin = -1, ymax = OUTER_VAL), color = "black", fill = NA, alpha = 0.5) +
    coord_flip() +
    facet_wrap(emotion_label ~ ., ncol = 3) +
    theme_bw() +
    theme(
      legend.position = 'none',
      panel.grid.major = element_blank(),
      panel.grid.minor = element_blank(),
      strip.background = element_blank(),
      axis.title = element_text(size = TEXT_SIZE),
      axis.text = element_text(size = TEXT_SIZE, color = 'black'),
      strip.text = element_text(face = 'bold', size = TEXT_SIZE),
      panel.border = element_blank(),
      axis.line = element_line(colour = "black")
    ) +
    labs(
      x = '',
      y = ''
    ) +
    scale_color_viridis_d(option = 'B') +
    ylim(-OUTER_VAL, OUTER_VAL)

# Combine the plots
variability_plot <- ggpubr::ggarrange(
  ggpubr::ggarrange(
    corpus_example_mapping,
    zoomed_in_plot,
    labels = c("a", "c"),
    font.label = list(size = 8, family = 'Whitney Semibold'),
    nrow = 2,
    heights = c(1, 2)
  ),
  variability_overview_plot,
  ncol = 2,
  labels = c("", "b"),
  font.label = list(size = 8, family = 'Whitney Semibold'),
  widths = c(1, 2)
)

ggsave(plot = variability_plot, '../../docs/figures/fig2_variability.pdf', device = cairo_pdf, units = 'mm', width = 175, height = 100)
