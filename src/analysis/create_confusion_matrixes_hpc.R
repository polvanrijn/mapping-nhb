# Run on the HPC as it takes a while!
library(brms)

save_confusion_matrix <- function(model, dat, save_path) {
  emo_levels <- levels(dat$emotion)
  pred_emo <- predict(model, dat)

  pred_emo_labs <- factor(apply(pred_emo, 1, function(x) emo_levels[which.max(x)]), levels = emo_levels)
  conv_mat <- caret::confusionMatrix(pred_emo_labs, dat$emotion)
  saveRDS(conv_mat, save_path)
}

# Create the confusion matrices
for (model_name in c('base_model', 'culture_model', 'big_model')) {
  model <- readRDS(paste0(model_name, '.RDS'))
  save_confusion_matrix(model, model$data, paste0(model_name, '_conf_mat.RDS'))
}
