"""All tunable thresholds in one place, so the team tunes numbers here instead of inside the modules.
Change a value, rerun, and every gate / measurement / verdict picks it up."""

CONFIG = {
    "image_max_side": 1024,  # photos are downscaled to this before any CV work
    "gate1": {
        "orb_features": 3000,
        "ratio_test": 0.75,  # Lowe ratio test for ORB matches
        "ransac_px": 5.0,  # RANSAC reprojection error in pixels
        "min_inliers": 25,
        "min_inlier_ratio": 0.25,
        "max_gps_distance_m": 50,  # only used when both photos have GPS
        "max_heading_diff_deg": 60,  # only used when both photos have compass heading
    },
    "gate2": {
        "duplicate_max_distance": 2,  # pHash distance at or below this = same photo resubmitted
        "history_dir": "data/history",  # earlier submissions to check the after photo against
    },
    "measure": {
        "texture_window": 21,  # window (px) for local texture (std-dev)
        "rough_k": 1.8,  # "rough" = texture above rough_k x median texture of the before photo
        "rough_floor": 6.0,  # minimum texture value to count as rough
        "close_px": 25,  # morphology size used to join rough pixels into one defect blob
        "diff_threshold": 40,  # grey-level change (after CLAHE) that counts as "changed"
        "smooth_ratio": 0.6,  # after texture below this x before texture = surface got smoother
        "min_defect_area_pct": 0.5,  # defect blob must cover at least this % of the before photo
        "min_coverage": 0.5,  # after photo must show at least this fraction of the defect
    },
    "verdict": {
        "verified_max_residual_pct": 15,
        "partial_max_residual_pct": 60,
    },
    "narrate": {
        "model": "gemma4:e2b",
        "timeout_s": 180,
    },
}
