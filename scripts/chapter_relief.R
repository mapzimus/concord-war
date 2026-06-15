#!/usr/bin/env Rscript
# chapter_relief.R — render one shaded-relief map per story chapter, replacing the
# flat matplotlib chapter maps. Reads the SAME app GeoJSONs the live explorer uses
# (static/data/*.geojson + manifest.json + chapters.json) and drapes each chapter's
# layers over a hillshade built from the project DEM. Output: static/story/<id>.png.
#
# Style matches scripts/R/hero_relief.R in the poster repo: hypsometric tint +
# multidirectional hillshade, a parchment "focus mask" outside the city, fixed-colour
# vector layers from the manifest, ggspatial scale/north, magick aged frame.

suppressMessages(suppressWarnings({
  library(sf); library(terra); library(ggplot2); library(ggspatial)
  library(ggnewscale); library(magick); library(jsonlite)
}))
ok_repel <- requireNamespace("ggrepel", quietly = TRUE)
ok_show  <- requireNamespace("showtext", quietly = TRUE) && requireNamespace("sysfonts", quietly = TRUE)

WAR  <- "C:/Users/Calen/concord-war"
DATA <- file.path(WAR, "static/data")
STORY <- file.path(WAR, "static/story"); dir.create(STORY, showWarnings = FALSE, recursive = TRUE)
DEM  <- "C:/Users/Calen/concord-civil-war-map/data/raw/dem/concord_dem_32145.tif"
CRSc <- 32145

PAPER <- "#f2e8cf"; INK <- "#2c2417"
WEST <- "#2f5d80"; EAST <- "#9e3b2e"; CONTEST <- "#c4825a"; WATER <- "#34657f"; FRONT <- "#1c1206"
ARC <- c(bombardment = "#b5402f", air_assault = "#356c92", armor = "#6e4a1f")
CAT_COL <- c(medical = "#c0392b", education = "#2e86c1", government = "#6e2c00", power = "#f1c40f",
             water = "#1f618d", transport = "#196f3d", logistics = "#b9770e", public_safety = "#884ea0",
             worship = "#7d6608", comms = "#117a65", fuel = "#d35400", civic = "#5d6d7e", military = "#4a1c1c")
SIDE_COL <- c(West = WEST, East = EAST)
EXP_COL  <- c(heavy = "#9e3b2e", partial = "#d68a3c", sheltered = "#5f8f5a")
FOREST <- "#5f7350"

fam_disp <- "serif"; fam_body <- "serif"
if (ok_show) try({
  sysfonts::font_add_google("Cinzel", "cinzel"); sysfonts::font_add_google("EB Garamond", "garamond")
  showtext::showtext_auto(); showtext::showtext_opts(dpi = 150)
  fam_disp <- "cinzel"; fam_body <- "garamond"
}, silent = TRUE)

halo <- function(size, weight = "plain", color = INK, lw = 2.2)
  list(size = size, fontface = weight, colour = color, family = fam_body)

manifest <- fromJSON(file.path(DATA, "manifest.json"), simplifyVector = FALSE)$layers
style_by <- setNames(lapply(manifest, function(l) l$style), sapply(manifest, function(l) l$id))
geojson_by <- setNames(sapply(manifest, function(l) l$geojson), sapply(manifest, function(l) l$id))
chapters <- fromJSON(file.path(DATA, "chapters.json"), simplifyVector = FALSE)$chapters
render_only <- commandArgs(trailingOnly = TRUE)  # optional: render only these chapter ids

# ---- relief (computed once on the full DEM) --------------------------------
dem <- rast(DEM); crs(dem) <- paste0("EPSG:", CRSc)
slope <- terrain(dem, "slope", unit = "radians"); aspect <- terrain(dem, "aspect", unit = "radians")
hs <- Reduce("+", shade(slope, aspect, angle = c(35, 35, 40), direction = c(270, 315, 350))) / 3
hdf_all <- as.data.frame(hs, xy = TRUE); names(hdf_all)[3] <- "hs"
edf_all <- as.data.frame(dem, xy = TRUE); names(edf_all)[3] <- "z"

# ---- vector layers ---------------------------------------------------------
TF <- function(lon, lat) as.numeric(st_coordinates(st_transform(st_sfc(st_point(c(lon, lat)), crs = 4326), CRSc)))
geo_cache <- new.env()
load_geo <- function(id) {
  if (exists(id, geo_cache)) return(get(id, geo_cache))
  f <- geojson_by[[id]]
  if (is.null(f) || !nzchar(f)) { assign(id, NULL, geo_cache); return(NULL) }
  p <- file.path(DATA, f)
  g <- tryCatch(suppressWarnings(st_zm(st_transform(st_read(p, quiet = TRUE), CRSc))), error = function(e) NULL)
  assign(id, g, geo_cache); g
}
city  <- load_geo("city"); river <- load_geo("river"); front <- load_geo("front_line")
forest <- load_geo("forest"); wbodies <- load_geo("water_bodies")
streams <- load_geo("streams"); roads_maj <- load_geo("roads_major")

HALFLAT <- c("10" = 0.125, "11" = 0.066, "12" = 0.040, "13" = 0.024)
SKIP_CTX <- c("city", "river", "front_line", "terrain_3d",
              "forest", "water_bodies", "streams", "roads_major")

# returns list(geoms = <ggplot layers>, labels = data.frame(x,y,text,col))
draw_layer <- function(lid, gdf) {
  if (is.null(gdf) || !nrow(gdf)) return(list(geoms = list(), labels = NULL))
  st <- style_by[[lid]]; if (is.null(st)) st <- list()
  gtype <- as.character(sf::st_geometry_type(gdf, by_geometry = FALSE))
  geoms <- list(); labs <- NULL

  # --- special-cased layers ---
  if (lid == "forest") {
    return(list(geoms = list(geom_sf(data = gdf, fill = FOREST, colour = NA, alpha = 0.4)), labels = NULL))
  }
  if (lid == "water_bodies") {
    return(list(geoms = list(geom_sf(data = gdf, fill = "#3f6f8c", colour = "#2c5066",
                                     linewidth = 0.2, alpha = 0.85)), labels = NULL))
  }
  if (lid %in% c("allied_towns", "neighborhoods")) {
    keycol <- if (lid == "allied_towns") "side" else "exposure"
    pal <- if (lid == "allied_towns") SIDE_COL else EXP_COL
    cols <- unname(pal[as.character(gdf[[keycol]])]); cols[is.na(cols)] <- "#888888"
    a <- if (lid == "allied_towns") 0.3 else 0.5
    geoms <- list(geom_sf(data = gdf, fill = cols, colour = INK, linewidth = 0.4, alpha = a))
    nm <- intersect(c("name", "Name"), names(gdf))
    if (length(nm)) {
      cen <- suppressWarnings(sf::st_coordinates(sf::st_point_on_surface(gdf)))
      labs <- data.frame(x = cen[, 1], y = cen[, 2], text = as.character(gdf[[nm[1]]]),
                         col = if (lid == "allied_towns") cols else INK, stringsAsFactors = FALSE)
    }
    return(list(geoms = geoms, labels = labs))
  }

  if (grepl("POLY", gtype)) {
    fill <- switch(lid, territory_west = WEST, territory_east = EAST, territory_contested = CONTEST,
                   if (!is.null(st$fill)) st$fill else NA)
    if (lid == "territory_contested_stripes") {
      geoms <- list(geom_sf(data = gdf, fill = NA, colour = "#9e3b2e", linewidth = 0.4))
    } else if (!is.na(fill)) {
      op <- if (!is.null(st$fillOpacity)) st$fillOpacity else 0.5
      op <- min(op, 0.42)
      geoms <- list(geom_sf(data = gdf, fill = fill, colour = grDevices::adjustcolor(fill, 0.9),
                            linewidth = 0.5, alpha = op))
    } else {
      geoms <- list(geom_sf(data = gdf, fill = NA, colour = if (!is.null(st$line)) st$line else INK, linewidth = 0.6))
    }
  } else if (grepl("LINE", gtype)) {
    if (isTRUE(st$arc)) {
      for (i in seq_len(nrow(gdf))) {
        co <- sf::st_coordinates(gdf[i, ]); k <- gdf$kind[i]
        if (is.null(k) || is.na(k)) k <- "bombardment"
        d <- data.frame(x = co[1, 1], y = co[1, 2], xe = co[nrow(co), 1], ye = co[nrow(co), 2])
        geoms <- c(geoms, list(geom_curve(data = d, aes(x = x, y = y, xend = xe, yend = ye),
          curvature = 0.2, linewidth = 1.6, colour = ARC[[k]], inherit.aes = FALSE,
          arrow = arrow(length = unit(0.16, "in"), type = "closed"), lineend = "round")))
      }
    } else {
      col <- if (lid == "river") WATER else if (lid == "front_line") FRONT else if (!is.null(st$line)) st$line else INK
      lt  <- if (lid == "front_line") "11" else "solid"
      geoms <- list(geom_sf(data = gdf, colour = col, linewidth = if (!is.null(st$lineWidth)) st$lineWidth * 0.5 else 0.8, linetype = lt))
    }
  } else if (lid == "city_pois") {  # 187 POIs coloured by category, no labels
    cols <- unname(CAT_COL[as.character(gdf$category)]); cols[is.na(cols)] <- "#3a2f1d"
    geoms <- list(
      geom_sf(data = gdf, colour = PAPER, size = 1.9),
      geom_sf(data = gdf, colour = cols, size = 1.25))
    return(list(geoms = geoms, labels = NULL))
  } else {  # points
    col <- if (!is.null(st$point)) st$point else "#7b241c"
    pr <- if (!is.null(st$pointRadius)) st$pointRadius else 7
    sz <- pr / 2.2 + 1
    geoms <- list(
      geom_sf(data = gdf, colour = PAPER, size = sz + 0.9),
      geom_sf(data = gdf, colour = col, size = sz))
    nm <- intersect(c("name", "Name", "NAME"), names(gdf))
    if (length(nm)) {
      cen <- suppressWarnings(sf::st_coordinates(sf::st_centroid(gdf)))
      labs <- data.frame(x = cen[, 1], y = cen[, 2],
                         text = substr(as.character(gdf[[nm[1]]]), 1, 32), col = col, stringsAsFactors = FALSE)
      labs <- labs[!is.na(labs$text) & labs$text != "None" & labs$text != "", ]
    }
  }
  list(geoms = geoms, labels = labs)
}

# ---- render each chapter ---------------------------------------------------
for (idx in seq_along(chapters)) {
  ch <- chapters[[idx]]; cid <- ch$id
  if (length(render_only) && !(cid %in% render_only)) next
  cam <- ch$camera; z <- as.character(cam$zoom)
  hl <- if (!is.null(HALFLAT[[z]])) HALFLAT[[z]] else 0.066
  hlon <- hl * 1.78
  c1 <- TF(cam$center[[1]] - hlon, cam$center[[2]] - hl)
  c2 <- TF(cam$center[[1]] + hlon, cam$center[[2]] + hl)
  minx <- min(c1[1], c2[1]); maxx <- max(c1[1], c2[1]); miny <- min(c1[2], c2[2]); maxy <- max(c1[2], c2[2])

  # Regional alliance map: frame to all allied towns (they reach well past the city/DEM).
  if ("allied_towns" %in% unlist(ch$layers)) {
    at_g <- load_geo("allied_towns")
    if (!is.null(at_g)) {
      bb <- st_bbox(at_g)
      px <- as.numeric(bb["xmax"] - bb["xmin"]) * 0.04; py <- as.numeric(bb["ymax"] - bb["ymin"]) * 0.04
      minx <- as.numeric(bb["xmin"]) - px; maxx <- as.numeric(bb["xmax"]) + px
      miny <- as.numeric(bb["ymin"]) - py; maxy <- as.numeric(bb["ymax"]) + py
    }
  }

  hsub <- hdf_all[hdf_all$x >= minx & hdf_all$x <= maxx & hdf_all$y >= miny & hdf_all$y <= maxy, ]
  esub <- edf_all[edf_all$x >= minx & edf_all$x <= maxx & edf_all$y >= miny & edf_all$y <= maxy, ]
  aoip <- st_as_sfc(st_bbox(c(xmin = minx, xmax = maxx, ymin = miny, ymax = maxy), crs = st_crs(CRSc)))
  mask <- suppressWarnings(st_difference(aoip, st_make_valid(st_union(st_geometry(city)))))

  p <- ggplot() +
    geom_raster(data = esub, aes(x, y, fill = z)) +
    scale_fill_gradientn(colours = c("#4f5f44", "#74794f", "#9a9163", "#bfae82", "#d9c9a3", "#efe6cb"), guide = "none") +
    new_scale_fill() +
    geom_raster(data = hsub, aes(x, y, fill = hs), alpha = 0.55) +
    scale_fill_gradient(low = "#16120a", high = "#ffffff", guide = "none") +
    { if (length(mask)) geom_sf(data = mask, fill = PAPER, colour = NA, alpha = 0.6) else NULL } +
    geom_sf(data = city, fill = NA, colour = INK, linewidth = 0.7)

  labels <- NULL
  if (!is.null(forest)) p <- p + draw_layer("forest", forest)$geoms
  if (!is.null(wbodies)) p <- p + draw_layer("water_bodies", wbodies)$geoms
  if (!is.null(streams)) p <- p + draw_layer("streams", streams)$geoms
  if (!is.null(roads_maj)) p <- p + draw_layer("roads_major", roads_maj)$geoms
  if (!is.null(river)) p <- p + draw_layer("river", river)$geoms
  for (lid in unlist(ch$layers)) {
    if (lid %in% SKIP_CTX) next
    r <- draw_layer(lid, load_geo(lid))
    if (length(r$geoms)) p <- p + r$geoms
    if (!is.null(r$labels) && nrow(r$labels)) labels <- rbind(labels, r$labels)
  }
  if (!is.null(front)) p <- p + draw_layer("front_line", front)$geoms

  if (ok_repel && !is.null(labels) && nrow(labels)) {
    p <- p + ggrepel::geom_text_repel(data = labels, aes(x, y, label = text),
      colour = INK, family = fam_body, size = 3.1, bg.color = PAPER, bg.r = 0.12,
      max.overlaps = 30, min.segment.length = 0, segment.color = "#6b5a2a", seed = 1)
  }

  p <- p +
    annotation_scale(location = "bl", style = "ticks", text_family = fam_body, line_col = INK, text_col = INK) +
    annotation_north_arrow(location = "tr", style = north_arrow_minimal(text_family = fam_body, line_col = INK)) +
    coord_sf(xlim = c(minx, maxx), ylim = c(miny, maxy), expand = FALSE, datum = NA) +
    labs(title = paste0(sprintf("%02d  ", idx), ch$title), subtitle = ch$subtitle) +
    theme_void(base_family = fam_body) +
    theme(
      plot.background = element_rect(fill = PAPER, colour = NA),
      panel.background = element_rect(fill = PAPER, colour = NA),
      plot.title = element_text(family = fam_disp, size = 24, face = "bold", colour = INK, hjust = 0.01, margin = margin(t = 8, b = 1)),
      plot.subtitle = element_text(family = fam_body, size = 12, colour = "#5a4a2c", hjust = 0.01, margin = margin(b = 5)),
      plot.margin = margin(6, 8, 6, 8))

  out <- file.path(STORY, paste0(cid, ".png"))
  ggsave(out, p, width = 11, height = 8.2, dpi = 150, bg = PAPER)
  try({
    im <- image_read(out)
    im <- image_border(im, "#d8c597", "4x4"); im <- image_border(im, INK, "7x7")
    image_write(im, out)
  }, silent = TRUE)
  cat(sprintf("[%02d] %s -> %s.png\n", idx, cid, cid))
}
cat("done: relief chapter maps ->", STORY, "\n")
