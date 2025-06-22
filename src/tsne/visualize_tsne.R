# Load required libraries
library(ggplot2)
library(dplyr)
library(RColorBrewer)
library(ggrepel)
library(ggthemes)
library(xkcd)

# Read the t-SNE data
df_tsne <- read.csv("../../data/df_tsne.csv", stringsAsFactors = FALSE)

# Identify queries (comic_id = -1) and regular comics
df_tsne$is_query <- df_tsne$comic_id == -1

# Create opacity column based on category
df_tsne$opacity <- ifelse(df_tsne$category == "other", 0.4, 0.75)

# Create size column based on category
df_tsne$point_size <- ifelse(df_tsne$category == "other", 1.0, 2.8)

# Reorder categories alphabetically but with 'other' last
categories <- unique(df_tsne$category)
categories_ordered <- c(sort(categories[categories != "other"]), "other")
df_tsne$category <- factor(df_tsne$category, levels = categories_ordered)

# Create shape mapping for categories
n_categories <- length(categories_ordered)
available_shapes <- c(16, 15, 17, 18, 13, 9)
shapes <- available_shapes[1:n_categories]
names(shapes) <- categories_ordered
# Make 'other' category use a small circle
shapes["other"] <- 1

# Create a pleasing color palette
n_categories <- length(categories_ordered)
# Manually select good colors from Set1, skipping yellow and brown
set1_all <- RColorBrewer::brewer.pal(9, "Set1")
# Remove yellow (#FFFF33) and brown (#A65628), keep the rest including pink
good_colors <- set1_all[c(1, 2, 3, 4, 5, 8, 9)]  # Skip positions 6 (yellow) and 7 (brown)

# Use our selected colors, adding Set2 if we need more
if (n_categories-1 <= length(good_colors)) {
  colors <- good_colors[1:(n_categories-1)]
} else {
  colors <- c(good_colors, RColorBrewer::brewer.pal(n_categories-1-length(good_colors), "Set2"))
}

# Add grey for 'other' category
colors <- c(colors, "grey70")
names(colors) <- categories_ordered

# Create the base plot
p <- ggplot(df_tsne, aes(x = dim1, y = dim2, color = category, shape = category)) +
  # Plot regular points with varying opacity, size, and shape
  geom_point(aes(alpha = I(opacity), size = I(point_size))) +
  # Add border for query points (comic_id = -1)
  geom_point(data = df_tsne[df_tsne$is_query, ],
             aes(x = dim1, y = dim2),
             color = "black",
             size = 3.5,
             shape = 21,
             fill = NA,
             stroke = 1.5) +
  # Add labels for query points
  geom_text_repel(data = df_tsne[df_tsne$is_query, ],
                  aes(label = title),
                  color = "black",
                  size = 5,
                  fontface = "bold",
                  family = "xkcd",
                  box.padding = 0.5,
                  point.padding = 0.3) +
  # Apply the color and shape palettes
  scale_color_manual(values = colors) +
  scale_shape_manual(values = shapes) +
  # Set symmetric x-axis limits
  xlim(-75, 75) +
  # Override legend symbol sizes to match actual point sizes
  guides(
    color = guide_legend(override.aes = list(size = 2.8, alpha = 1)),
  ) +
  # Styling
  theme_xkcd() +
  theme(
    plot.title = element_text(size = 18, hjust = 0.5),
    axis.title = element_text(size = 14),
    axis.text = element_blank(),
    axis.ticks = element_blank(),
    legend.title = element_text(size = 15),
    legend.text = element_text(size = 15),
    legend.position = c(0.02, 0.98),
    legend.justification = c(0, 1),
    legend.background = element_rect(fill = "transparent", color = NA),
    legend.margin = margin(8, 8, 8, 8)
  ) +
  labs(
    title = "XKCD Comics in Embedding Space (t-SNE Transformed)",
    x = "Dimension 1",
    y = "Dimension 2",
    color = "Query",
    shape = "Query"
  )

# Print the plot
print(p)

# Save the plot
ggsave("tsne_visualization.png", plot = p, width = 14, height = 10, dpi = 300)
ggsave("tsne_visualization2.png", plot = p, width = 14, dpi = 300)
cat("Plot saved as 'tsne_visualization.png'\n")
