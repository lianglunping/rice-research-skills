# ggplot2 passes linewidth * .pt to grid. Standard R PDF devices
# interpret grid lwd = 1 as 0.75 pt. The ragg PNG device uses 1/96 in.
publication_linewidth <- function(points) {
  points / (0.75 * ggplot2::.pt)
}

publication_axis_linewidth <- publication_linewidth(0.75)
publication_curve_linewidth <- publication_linewidth(1)
publication_error_linewidth <- publication_linewidth(0.75)

publication_theme <- function(font_family = "Arial") {
  ggplot2::theme_classic(base_family = font_family, base_size = 8) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(size = 8),
      plot.tag = ggplot2::element_text(size = 9, face = "bold"),
      axis.title = ggplot2::element_text(size = 8),
      axis.text = ggplot2::element_text(size = 7, colour = "black"),
      axis.line = ggplot2::element_line(linewidth = publication_axis_linewidth),
      axis.ticks = ggplot2::element_line(linewidth = publication_axis_linewidth),
      legend.title = ggplot2::element_text(size = 8),
      legend.text = ggplot2::element_text(size = 8),
      strip.text = ggplot2::element_text(size = 8),
      panel.grid = ggplot2::element_blank()
    )
}

save_publication_figure <- function(plot, filename, width_mm, height_mm, dpi = 300,
                                    pdf_device = c("cairo", "quartz")) {
  extension <- tolower(tools::file_ext(filename))
  if (!extension %in% c("pdf", "png")) {
    stop("filename must end in .pdf or .png")
  }
  for (value in list(width_mm, height_mm, dpi)) {
    if (!is.numeric(value) || length(value) != 1L || !is.finite(value) || value <= 0) {
      stop("width_mm, height_mm and dpi must be finite positive numbers")
    }
  }

  previous_device <- grDevices::dev.cur()
  if (extension == "pdf") {
    pdf_device <- match.arg(pdf_device)
    if (pdf_device == "quartz") {
      grDevices::quartz(type = "pdf", file = filename, width = width_mm / 25.4,
                        height = height_mm / 25.4, bg = "white")
    } else {
      grDevices::cairo_pdf(filename = filename, width = width_mm / 25.4,
                           height = height_mm / 25.4, bg = "white", fallback_resolution = dpi)
    }
  } else {
    ragg::agg_png(filename = filename, width = width_mm, height = height_mm,
                  units = "mm", res = dpi, background = "white")
  }
  if (grDevices::dev.cur() == previous_device) {
    stop("Could not open the requested graphics device")
  }
  on.exit(grDevices::dev.off())
  if (inherits(plot, "grob")) {
    grid::grid.newpage()
    grid::grid.draw(plot)
  } else {
    print(plot)
  }
  invisible(filename)
}
