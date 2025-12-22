"""
Enhanced SQL Generator Dialog with Comprehensive Smart Autocomplete
Supports ALL climate and earth observation attributes
Natural language patterns like:
- "I want Land Surface Temperature..."
- "Show me NDVI data..."
- "Give me precipitation for Cairo..."
"""

import customtkinter as ctk
from typing import List
import re


class AIAutocompleteSuggestion:
    """Represents an AI autocomplete suggestion"""
    def __init__(self, text: str, description: str = "", score: float = 100.0):
        self.text = text
        self.description = description
        self.score = score


class AIAutocompleteEngine:
    """Comprehensive autocomplete engine for natural language AI queries"""
    
    # Command starters
    STARTERS = [
        "I want", "I need", "Show me", "Give me", "Get", "Find", 
        "Fetch", "Display", "Retrieve", "Query", "Select", "Extract",
        "Download", "Analyze", "Compare", "Monitor"
    ]
    
    # ALL Data types / measurements (COMPREHENSIVE)
    MEASUREMENTS = [
        # Temperature (all variations)
        "Land Surface Temperature", "LST", "temperature", "temp",
        "surface temperature", "air temperature", "soil temperature",
        "minimum temperature", "maximum temperature", "mean temperature",
        "dewpoint temperature", "skin temperature",
        "temperature at 2m", "temperature 2m", "temperature_2m",
        "temperature_2m_max", "temperature_2m_min",
        "LST_Day_1km", "LST_Night_1km",
        
        # Precipitation (all variations)
        "precipitation", "rainfall", "rain", "total precipitation",
        "total_precipitation", "convective precipitation",
        "snow", "snowfall", "snow depth", "snow cover", "snow_depth",
        "precip", "Rainf_f_tavg", "Snowf_tavg",
        
        # Humidity & Moisture (all variations)
        "humidity", "relative humidity", "specific humidity", "absolute humidity",
        "relative_humidity", "specific_humidity", "RH_inst", "Qair_f_inst",
        "soil moisture", "volumetric soil water", "surface soil moisture",
        "soil_moisture", "volumetric_soil_water_layer_1", "volumetric_soil_water_layer_2",
        "volumetric_soil_water_layer_3", "volumetric_soil_water_layer_4",
        "SoilMoi0_10cm_inst", "SoilMoi10_40cm_inst", "SoilMoi40_100cm_inst",
        "water vapor", "water vapour", "dewpoint", "total_column_water_vapour",
        
        # Wind (all variations)
        "wind speed", "wind", "wind direction", "wind gust",
        "wind_speed", "wind_speed_10m", "wind_speed_100m",
        "wind_direction", "wind_direction_10m", "wind_direction_100m",
        "u wind component", "v wind component", "surface wind",
        "u_component_of_wind_10m", "v_component_of_wind_10m",
        "u_component_of_wind_100m", "v_component_of_wind_100m",
        "Wind_f_inst", "wind at 10m", "wind at 100m",
        
        # Vegetation Indices (all)
        "NDVI", "vegetation index", "greenness", 
        "EVI", "EVI2", "Enhanced Vegetation Index",
        "SAVI", "MSAVI", "MSAVI2",
        "NDWI", "Normalized Difference Water Index",
        "NDMI", "Normalized Difference Moisture Index",
        "NBR", "NBR2", "Normalized Burn Ratio",
        "leaf area index", "LAI", "GCI", "ARVI", "SIPI", "BSI",
        
        # Evapotranspiration (all)
        "evapotranspiration", "ET", "evaporation",
        "potential evapotranspiration", "PET",
        "actual evapotranspiration", "AET",
        "Evap_tavg", "PotEvap_tavg",
        "evaporation_from_bare_soil",
        "evaporation_from_vegetation_transpiration",
        
        # Radiation (all)
        "solar radiation", "radiation", "shortwave radiation",
        "longwave radiation", "net radiation",
        "surface solar radiation", "thermal radiation",
        "surface_solar_radiation_downwards",
        "surface_thermal_radiation_downwards",
        "surface_net_solar_radiation",
        "SWdown_f_tavg", "LWdown_f_tavg",
        
        # Pressure (all)
        "pressure", "surface pressure", "atmospheric pressure",
        "sea level pressure", "mean sea level pressure",
        "surface_pressure", "Psurf_f_inst",
        
        # Cloud & Atmospheric (all)
        "cloud cover", "clouds", "total cloud cover",
        "total_cloud_cover", "low_cloud_cover", "high_cloud_cover",
        "aerosol optical depth", "AOD", "aerosol",
        "air quality", "PM2.5", "PM10",
        
        # Spectral Bands (all Sentinel-2)
        "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A",
        "B9", "B10", "B11", "B12",
        "blue band", "green band", "red band", 
        "NIR", "near infrared", "SWIR", "shortwave infrared",
        "Band 1", "Band 2", "Band 3", "Band 4", "Band 5",
        "Band 6", "Band 7", "Band 8", "Band 9", "Band 10",
        "Band 11", "Band 12", "thermal band", "cirrus",
        
        # Landsat Bands
        "SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7",
        "ST_B10", "QA_PIXEL", "QA_RADSAT",
        
        # MODIS Bands
        "sur_refl_b01", "sur_refl_b02", "sur_refl_b03", "sur_refl_b04",
        "sur_refl_b05", "sur_refl_b06", "sur_refl_b07",
        
        # Elevation & Terrain
        "elevation", "altitude", "DEM", "Digital Elevation Model",
        "slope", "aspect", "hillshade", "terrain",
        
        # Land Cover
        "land cover", "landcover", "land use", "classification",
        
        # Soil
        "soil temperature", "SoilTMP0_10cm_inst", "SoilTMP10_40cm_inst",
        
        # Runoff
        "runoff", "surface runoff", "subsurface runoff",
        "Qs_acc", "Qsb_acc",
        
        # Quality
        "QA60", "QA", "quality", "cloud mask", "pixel_qa",
        "QC_Day", "QC_Night",
        
        # Angles
        "ViewZenith", "SolarZenith", "RelativeAzimuth",
        "solar_azimuth", "solar_zenith", "view_azimuth",
        
        # Other
        "albedo", "reflectance", "emissivity", "Emis_31", "Emis_32",
        "population", "population density", "nightlights",
        "lake cover", "lake depth", "Tair_f_inst", "AvgSurfT_inst",
    ]
    
    # Datasets
    DATASETS = [
        "ERA5", "ERA5 Land", "ERA5_LAND", "ERA5 data",
        "Sentinel-2", "Sentinel 2", "S2", "Sentinel2", "S2_SR",
        "Sentinel-1", "Sentinel 1", "S1", "Sentinel1", "S1_GRD",
        "Landsat", "Landsat 8", "Landsat 9", "Landsat 7", "Landsat 5",
        "LC08", "LC09", "LE07", "LT05",
        "MODIS", "MODIS vegetation", "MODIS LST", "MODIS NDVI",
        "MOD13A1", "MOD13Q1", "MYD13A1", "MOD11A1", "MOD11A2",
        "CHIRPS", "CHIRPS precipitation", "CHIRPS daily",
        "SRTM", "SRTM elevation", "DEM data", "SRTM_90",
        "GPM", "GPM precipitation",
        "GLDAS", "GRACE",
        "Dynamic World", "ESA WorldCover", "WorldCover",
    ]
    
    # Egyptian locations (comprehensive)
    LOCATIONS = [
        # Major cities
        "Cairo", "Alexandria", "Giza", "Suez", "Port Said",
        "Luxor", "Aswan", "Hurghada", "Sharm El Sheikh",
        "Mansoura", "Tanta", "Ismailia", "Fayoum",
        "Minya", "Sohag", "Qena", "Asyut", "Zagazig",
        "Damietta", "Beni Suef", "Assiut", "Kafr El Sheikh",
        
        # Regions
        "Egypt", "Nile Delta", "Upper Egypt", "Lower Egypt",
        "Sinai", "North Sinai", "South Sinai",
        "Western Desert", "Eastern Desert", "Libyan Desert",
        "Red Sea", "Mediterranean", "Mediterranean coast",
        "Nile Valley", "Nile River",
        
        # Governorates
        "Cairo Governorate", "Giza Governorate", "Qalyubia",
        "Sharqia", "Dakahlia", "Beheira", "Gharbia",
        "Monufia", "Kafr El Sheikh Governorate", "Damietta Governorate",
    ]
    
    # Time expressions (comprehensive)
    TIME_EXPRESSIONS = [
        # Prepositions
        "from", "to", "between", "during", "in", "for", "since", "until",
        
        # Months (full)
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
        
        # Months (abbreviated)
        "Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        
        # Years
        "2024", "2023", "2022", "2021", "2020", "2019", "2018",
        "2017", "2016", "2015",
        
        # Relative time
        "last month", "last year", "this month", "this year",
        "last week", "this week", "yesterday", "today",
        "past month", "past year", "recent",
        
        # Seasons
        "summer", "winter", "spring", "autumn", "fall",
        "dry season", "wet season", "rainy season",
    ]
    
    # Scale/resolution (comprehensive)
    SCALES = [
        "at 10m", "10m resolution", "10 meter",
        "at 30m", "30m resolution", "30 meter",
        "at 100m", "100m resolution", "100 meter",
        "at 250m", "250m resolution", "250 meter",
        "at 500m", "500m resolution", "500 meter",
        "at 1km", "1km resolution", "1 kilometer",
        "high resolution", "low resolution", "medium resolution",
    ]
    
    # Coordinates
    COORDINATE_HINTS = [
        "latitude", "longitude", "lat", "lon",
        "coordinates", "location at",
        "north", "south", "east", "west",
    ]
    
    # Aggregations & Operations
    OPERATIONS = [
        "average", "mean", "median", "sum", "total",
        "minimum", "maximum", "min", "max", "count",
        "standard deviation", "std", "variance",
        "monthly average", "yearly average", "daily average",
        "group by", "order by", "where", "filtered by",
    ]
    
    # Common phrases
    COMMON_PHRASES = [
        "data for", "information about", "statistics for",
        "time series", "cloud free", "clear sky",
        "export as CSV", "save as", "download",
    ]
    
    def __init__(self):
        self.all_suggestions = []
        self._build_suggestion_database()
    
    def _build_suggestion_database(self):
        """Build comprehensive suggestion database"""
        self.all_suggestions = []
        
        # Add all types
        for starter in self.STARTERS:
            self.all_suggestions.append(AIAutocompleteSuggestion(starter, "Command", 100.0))
        
        for measure in self.MEASUREMENTS:
            self.all_suggestions.append(AIAutocompleteSuggestion(measure, "Measurement", 95.0))
        
        for dataset in self.DATASETS:
            self.all_suggestions.append(AIAutocompleteSuggestion(dataset, "Dataset", 93.0))
        
        for loc in self.LOCATIONS:
            self.all_suggestions.append(AIAutocompleteSuggestion(loc, "Location", 90.0))
        
        for time_exp in self.TIME_EXPRESSIONS:
            self.all_suggestions.append(AIAutocompleteSuggestion(time_exp, "Time", 85.0))
        
        for scale in self.SCALES:
            self.all_suggestions.append(AIAutocompleteSuggestion(scale, "Resolution", 80.0))
        
        for coord in self.COORDINATE_HINTS:
            self.all_suggestions.append(AIAutocompleteSuggestion(coord, "Coordinate", 75.0))
        
        for op in self.OPERATIONS:
            self.all_suggestions.append(AIAutocompleteSuggestion(op, "Operation", 70.0))
        
        for phrase in self.COMMON_PHRASES:
            self.all_suggestions.append(AIAutocompleteSuggestion(phrase, "Phrase", 65.0))
    
    def get_suggestions(self, text: str, cursor_pos: int) -> List[AIAutocompleteSuggestion]:
        """Get context-aware suggestions - FIXED MATCHING"""
        if not text.strip():
            return [s for s in self.all_suggestions if s.description == "Command"][:10]
        
        # Get current word
        words_before = text[:cursor_pos].split()
        current_word = words_before[-1] if words_before else ""
        
        text_lower = text.lower()
        context = self._determine_context(text_lower)
        
        # Get suggestions based on context
        suggestions = []
        
        if context == "starter":
            suggestions = [s for s in self.all_suggestions if s.description == "Command"]
        elif context == "measurement":
            suggestions = [s for s in self.all_suggestions if s.description in ["Measurement", "Dataset"]]
        elif context == "dataset":
            suggestions = [s for s in self.all_suggestions if s.description == "Dataset"]
        elif context == "location":
            suggestions = [s for s in self.all_suggestions if s.description == "Location"]
        elif context == "time":
            suggestions = [s for s in self.all_suggestions if s.description == "Time"]
        elif context == "scale":
            suggestions = [s for s in self.all_suggestions if s.description == "Resolution"]
        elif context == "operation":
            suggestions = [s for s in self.all_suggestions if s.description == "Operation"]
        else:
            suggestions = self.all_suggestions
        
        # IMPROVED FILTERING - show more results
        if current_word and len(current_word) >= 1:  # Changed from 2 to 1
            filtered = []
            current_lower = current_word.lower()
            
            for sugg in suggestions:
                # More flexible matching
                if self._flexible_match(sugg.text, current_lower):
                    score = self._calculate_match_score(sugg.text, current_lower)
                    sugg_copy = AIAutocompleteSuggestion(sugg.text, sugg.description, score)
                    filtered.append(sugg_copy)
            suggestions = filtered
        
        # Sort and return top results
        suggestions.sort(key=lambda s: s.score, reverse=True)
        return suggestions[:20]  # Show top 20
    
    def _flexible_match(self, text: str, partial: str) -> bool:
        """More flexible matching - FIXED"""
        if not partial:
            return True
        
        text_lower = text.lower()
        partial_lower = partial.lower()
        
        # Direct matches
        if text_lower.startswith(partial_lower):
            return True
        
        if partial_lower in text_lower:
            return True
        
        # Word boundary match
        words = text_lower.split()
        for word in words:
            if word.startswith(partial_lower):
                return True
        
        # Match with underscores (e.g., "temp" matches "temperature_2m")
        if '_' in text_lower:
            parts = text_lower.split('_')
            for part in parts:
                if part.startswith(partial_lower):
                    return True
        
        # Abbreviation match (e.g., "prec" matches "precipitation")
        if len(partial_lower) >= 3:
            if text_lower.startswith(partial_lower[:3]):
                return True
        
        return False
    
    def _determine_context(self, text: str) -> str:
        """Determine context"""
        if not text or len(text.split()) <= 2:
            return "starter"
        
        words = text.split()
        last_words = " ".join(words[-3:]) if len(words) >= 3 else text
        
        if any(s in text for s in ["i want", "show me", "give me", "get", "find"]):
            if not any(m.lower() in text for m in ["temperature", "precipitation", "humidity", "wind", "ndvi"]):
                return "measurement"
        
        if any(w in last_words for w in ["from", "using", "with"]):
            if not any(d.lower() in text for d in ["era5", "sentinel", "landsat", "modis"]):
                return "dataset"
        
        if any(w in last_words for w in ["for", "in", "at", "near"]):
            if not any(l.lower() in text for l in ["cairo", "egypt", "alexandria"]):
                return "location"
        
        if any(w in last_words for w in ["from", "to", "between", "during"]):
            return "time"
        
        if "resolution" in last_words or "scale" in last_words:
            return "scale"
        
        if any(w in last_words for w in ["calculate", "average", "group", "sort"]):
            return "operation"
        
        return "general"
    
    def _calculate_match_score(self, text: str, partial: str) -> float:
        """Calculate match score - IMPROVED"""
        text_lower = text.lower()
        partial_lower = partial.lower()
        
        # Exact start - highest score
        if text_lower.startswith(partial_lower):
            coverage = len(partial_lower) / max(len(text_lower), 1)
            return 100.0 + (coverage * 50)
        
        # Contains match
        if partial_lower in text_lower:
            pos = text_lower.index(partial_lower)
            return 70.0 + (1.0 - pos / max(len(text_lower), 1)) * 20
        
        # Word match
        words = text_lower.split()
        for i, word in enumerate(words):
            if word.startswith(partial_lower):
                return 60.0 - (i * 5)
        
        # Underscore parts match
        if '_' in text_lower:
            parts = text_lower.split('_')
            for i, part in enumerate(parts):
                if part.startswith(partial_lower):
                    return 50.0 - (i * 3)
        
        return 10.0


class AIAutocompletePopup(ctk.CTkToplevel):
    """Popup for AI autocomplete suggestions"""
    
    TYPE_COLORS = {
        'Command': '#569CD6', 'Measurement': '#9CDCFE', 'Dataset': '#4EC9B0',
        'Location': '#C586C0', 'Time': '#CE9178', 'Resolution': '#B5CEA8',
        'Coordinate': '#DCDCAA', 'Operation': '#D4D4D4', 'Phrase': '#808080',
    }
    
    def __init__(self, parent, suggestions: List[AIAutocompleteSuggestion], 
                 on_select, x: int, y: int):
        super().__init__(parent)
        
        self.on_select = on_select
        self.suggestions = suggestions
        self.selected_index = 0
        
        self.withdraw()
        self.overrideredirect(True)
        self.configure(fg_color="#1E1E1E")
        
        main_container = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=0)
        main_container.pack(fill="both", expand=True)
        
        header = ctk.CTkFrame(main_container, fg_color="#252526", height=30, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(header, text="💡 AI Suggestions", font=("Consolas", 11, "bold"), 
                            text_color="#CCCCCC", anchor="w")
        title.pack(side="left", padx=10, pady=5)
        
        close_btn = ctk.CTkButton(header, text="✕", width=30, height=25, 
                                 fg_color="transparent", hover_color="#E81123",
                                 text_color="#CCCCCC", font=("Consolas", 16, "bold"),
                                 corner_radius=0, command=self.destroy)
        close_btn.pack(side="right", padx=5, pady=2)
        
        max_height = min(350, len(suggestions) * 32 + 10)
        self.scroll_frame = ctk.CTkScrollableFrame(main_container, width=500, 
                                                    height=max_height, fg_color="#1E1E1E")
        self.scroll_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.suggestion_buttons = []
        for idx, sugg in enumerate(suggestions):
            self._create_suggestion_item(idx, sugg)
        
        self.geometry(f"+{x}+{y + 20}")
        self.deiconify()
        self.lift()
        
        if self.suggestion_buttons:
            self._highlight_item(0)
    
    def _create_suggestion_item(self, idx: int, sugg: AIAutocompleteSuggestion):
        """Create suggestion button"""
        item_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", height=30)
        item_frame.pack(fill="x", pady=1)
        item_frame.pack_propagate(False)
        
        type_color = self.TYPE_COLORS.get(sugg.description, '#9CDCFE')
        
        btn = ctk.CTkButton(item_frame, text=sugg.text, anchor="w",
                           fg_color="transparent", hover_color="#2D2D30",
                           text_color=type_color, font=("Consolas", 11),
                           command=lambda: self._select_item(idx))
        btn.pack(side="left", fill="both", expand=True, padx=5)
        
        type_badge = ctk.CTkLabel(item_frame, text=sugg.description[:3].upper(),
                                 width=35, height=22, fg_color=type_color,
                                 text_color="#1E1E1E", font=("Consolas", 8, "bold"),
                                 corner_radius=3)
        type_badge.pack(side="right", padx=5)
        
        self.suggestion_buttons.append((btn, item_frame, sugg))
    
    def _highlight_item(self, index: int):
        for btn, frame, _ in self.suggestion_buttons:
            btn.configure(fg_color="transparent")
        
        if 0 <= index < len(self.suggestion_buttons):
            btn, frame, _ = self.suggestion_buttons[index]
            btn.configure(fg_color="#2D2D30")
            self.selected_index = index
            frame.update_idletasks()
            self.scroll_frame._parent_canvas.yview_moveto(index / len(self.suggestion_buttons))
    
    def _select_item(self, index: int):
        if 0 <= index < len(self.suggestions):
            self.on_select(self.suggestions[index].text)
            self.destroy()
    
    def move_selection_up(self):
        self._highlight_item(max(0, self.selected_index - 1))
    
    def move_selection_down(self):
        self._highlight_item(min(len(self.suggestions) - 1, self.selected_index + 1))
    
    def select_current(self):
        self._select_item(self.selected_index)


class AIAutocompleteTextbox:
    """Wrapper for textbox with AI autocomplete"""
    
    def __init__(self, textbox: ctk.CTkTextbox):
        self.textbox = textbox
        self.engine = AIAutocompleteEngine()
        self.popup = None
        
        self.textbox.bind('<KeyRelease>', self._on_key_release)
        self.textbox.bind('<Control-space>', self._on_ctrl_space)
        self.textbox.bind('<Escape>', self._on_escape)
        self.textbox.bind('<Up>', self._on_up_arrow)
        self.textbox.bind('<Down>', self._on_down_arrow)
        self.textbox.bind('<Return>', self._on_return)
        self.textbox.bind('<Tab>', self._on_tab)
    
    def _on_key_release(self, event):
        if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Return', 'Escape', 'Tab']:
            return
        self._show_autocomplete()
    
    def _on_ctrl_space(self, event):
        self._show_autocomplete()
        return "break"
    
    def _on_escape(self, event):
        if self.popup:
            self.popup.destroy()
            self.popup = None
            return "break"
    
    def _on_up_arrow(self, event):
        if self.popup:
            self.popup.move_selection_up()
            return "break"
    
    def _on_down_arrow(self, event):
        if self.popup:
            self.popup.move_selection_down()
            return "break"
    
    def _on_return(self, event):
        if self.popup:
            self.popup.select_current()
            return "break"
    
    def _on_tab(self, event):
        if self.popup:
            self.popup.select_current()
            return "break"
    
    def _show_autocomplete(self):
        if self.popup:
            self.popup.destroy()
            self.popup = None
        
        cursor_index = self.textbox.index("insert")
        row, col = map(int, cursor_index.split('.'))
        
        all_text = self.textbox.get("1.0", "end-1c")
        lines = all_text.split('\n')
        cursor_pos = sum(len(line) + 1 for line in lines[:row-1]) + col
        
        suggestions = self.engine.get_suggestions(all_text, cursor_pos)
        
        if not suggestions:
            return
        
        bbox = self.textbox.bbox(f"{row}.{col}")
        if bbox:
            x = self.textbox.winfo_rootx() + bbox[0]
            y = self.textbox.winfo_rooty() + bbox[1] + bbox[3]
            
            self.popup = AIAutocompletePopup(
                self.textbox, suggestions, self._insert_suggestion, x, y
            )
    
    def _insert_suggestion(self, text: str):
        cursor_index = self.textbox.index("insert")
        row, col = map(int, cursor_index.split('.'))
        
        line_text = self.textbox.get(f"{row}.0", f"{row}.end")
        
        word_start = col
        while word_start > 0:
            if line_text[word_start - 1] in ' \t\n':
                break
            word_start -= 1
        
        self.textbox.delete(f"{row}.{word_start}", cursor_index)
        self.textbox.insert(f"{row}.{word_start}", text)
        
        new_col = word_start + len(text)
        self.textbox.insert(f"{row}.{new_col}", " ")
        self.textbox.mark_set("insert", f"{row}.{new_col + 1}")
        
        if self.popup:
            self.popup.destroy()
            self.popup = None