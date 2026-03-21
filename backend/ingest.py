import os
import re
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Bike, KinematicCurve

SQLALCHEMY_DATABASE_URL = "sqlite:///./kinematics.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_gear_mapping(filenames):
    """
    Scans filenames to find gear ratios (e.g., 32x51), calculates the ratio,
    and returns the low gear (smallest ratio) and high gear (largest ratio).
    """
    gears = set()
    for f in filenames:
        match = re.search(r'_(\d+x\d+)\.csv', f)
        if match:
            gears.add(match.group(1))
            
    if not gears:
        return None, None
        
    gear_list = list(gears)
    # Sort by ratio: Chainring / Cog. 
    # Smallest ratio = Low gear (e.g., 32/51 = 0.62)
    # Largest ratio = High gear (e.g., 32/10 = 3.20)
    gear_list.sort(key=lambda g: int(g.split('x')[0]) / int(g.split('x')[1]))
    
    return gear_list[0], gear_list[-1]

def process_bike_folder(db, folder_path):
    folder_name = os.path.basename(folder_path)
    folder_parts = folder_name.split('_')
    
    if len(folder_parts) != 4:
        print(f"Skipping {folder_name}: Does not match 'Make_Model_Year_Design'.")
        return

    make, model, year, design = folder_parts

    # 1. Check if bike already exists
    if db.query(Bike).filter_by(make=make, model=model, year=int(year)).first():
        print(f"{make} {model} already in database. Skipping.")
        return

    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    if not csv_files:
        return

    # 2. Determine Gear Mapping
    gear_low, gear_high = get_gear_mapping(csv_files)
    
    # 3. Read and Merge CSVs
    dataframes = []
    for file in csv_files:
        file_path = os.path.join(folder_path, file)
        
        # na_values=['?'] safely handles Linkage's missing geometry data
        df = pd.read_csv(file_path, sep=';', na_values=['?'])

        # 1. IMMEDIATELY kill any ghost columns caused by trailing semicolons
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        if 'Travel' not in df.columns:
            continue
            
        # Parse the filename: "Atherton AM150 2024_Anti-squat_32x51.csv"
        file_parts = file.replace('.csv', '').split('_')

        # If it's a 2-column metric file (Travel + Metric)
        if len(df.columns) == 2 and len(file_parts) >= 2:
            metric = file_parts[1] # e.g., 'Anti-squat', 'Leverage Ratio'
            # Map the column based on the gear used
            if len(file_parts) == 3:
                gear = file_parts[2]
                if gear == gear_low:
                    col_name = f"{metric}_low"
                elif gear == gear_high:
                    col_name = f"{metric}_high"
                else:
                    col_name = f"{metric}_{gear}" # Fallback
            else:
                col_name = metric
                
            # Rename the second column to our standardized name
            df.rename(columns={df.columns[1]: col_name}, inplace=True)
            
        # 1. Force the Travel column to be numbers. Text becomes 'NaN' (Not a Number)
        df['Travel'] = pd.to_numeric(df['Travel'], errors='coerce')
        
        # 2. Drop any rows where Travel is NaN (this deletes the text footer)
        df.dropna(subset=['Travel'], inplace=True)

        # 3. Now it is safe to set the index
        df.set_index('Travel', inplace=True)
        
        # 4. Ensure the rest of the data is numeric too
        df = df.apply(pd.to_numeric, errors='coerce')
        dataframes.append(df)

    # Merge everything on the Travel index
    merged_df = pd.concat(dataframes, axis=1).reset_index()
    
    # FIX: Drop duplicate columns and 'ghost' columns caused by trailing semicolons
    merged_df = merged_df.loc[:, ~merged_df.columns.duplicated()]
    merged_df = merged_df.loc[:, ~merged_df.columns.str.contains('^Unnamed')]
    
    # 4. Calculate Derived Metrics
    max_travel = merged_df['Travel'].max()
    merged_df['travel_percent'] = (merged_df['Travel'] / max_travel) * 100

    progressivity = None
    if 'Leverage Ratio' in merged_df.columns:
        lr_start = merged_df['Leverage Ratio'].dropna().iloc[0]
        lr_end = merged_df['Leverage Ratio'].dropna().iloc[-1]
        progressivity = ((lr_start - lr_end) / lr_start) * 100

    avg_as = None
    if 'Anti-squat_low' in merged_df.columns:
        pedal_zone = merged_df[(merged_df['travel_percent'] >= 20) & (merged_df['travel_percent'] <= 40)]
        avg_as = pedal_zone['Anti-squat_low'].mean()

    avg_ar = None
    if 'Anti-rise_high' in merged_df.columns:
        squish_zone = merged_df[(merged_df['travel_percent'] >= 40) & (merged_df['travel_percent'] <= 100)]
        avg_ar = squish_zone['Anti-rise_high'].mean()

    # 5. Save Bike Metadata
    new_bike = Bike(
        make=make,
        model=model.replace("-", " "),
        year=int(year),
        suspension_design=design,
        gear_low=gear_low,
        gear_high=gear_high,
        avg_antisquat_pedaling=round(avg_as, 2) if pd.notna(avg_as) else None,
        progressivity_percent=round(progressivity, 2) if pd.notna(progressivity) else None,
        avg_antirise_squish=round(avg_ar, 2) if pd.notna(avg_ar) else None
    )
    db.add(new_bike)
    db.flush()

    # 6. Save Curve Points
    geometry_cols = ['RW_X', 'RW_Y', 'BB_X', 'BB_Y', 'FW_X', 'FW_Y', 'SHK1_X', 'SHK1_Y', 'SHK2_X', 'SHK2_Y', 'IC_X', 'IC_Y', 'CC_X', 'CC_Y']

    for _, row in merged_df.iterrows():
        # Package geometry safely into a JSON dictionary, ignoring NaNs
        geom_dict = {
            col: round(row[col], 3) 
            for col in geometry_cols 
            if col in merged_df.columns and pd.notna(row[col])
        }

        def get_val(col_name):
            return round(row[col_name], 3) if col_name in merged_df.columns and pd.notna(row[col_name]) else None

        point = KinematicCurve(
            bike_id=new_bike.id,
            travel_mm=get_val('Travel'),
            travel_percent=get_val('travel_percent'),
            leverage_ratio=get_val('Leverage Ratio'),
            anti_squat_low=get_val('Anti-squat_low'),
            anti_squat_high=get_val('Anti-squat_high'),
            anti_rise_low=get_val('Anti-rise_low'),
            anti_rise_high=get_val('Anti-rise_high'),
            pedal_kickback_low=get_val('Pedal-kickback_low'),
            pedal_kickback_high=get_val('Pedal-kickback_high'),
            chain_growth_low=get_val('Chain Growth_low'),
            chain_growth_high=get_val('Chain Growth_high'),
            forces=get_val('Forces'),
            shock_compression=get_val('Shock Compression'),
            axle_path_x=get_val('Axlepath X'), 
            axle_path_radius=get_val('Axle Path radius'),
            axle_path_steepness=get_val('Axle Path steepness'),
            geometry_data=geom_dict
        )
        db.add(point)

    db.commit()
    print(f"Successfully ingested {make} {model} ({gear_low} / {gear_high}) - {len(merged_df)} points.")

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    data_dir = "./data"
    
    if not os.path.exists(data_dir):
        print(f"Directory {data_dir} does not exist. Create it and add your bike folders.")
    else:
        for folder in os.listdir(data_dir):
            folder_path = os.path.join(data_dir, folder)
            if os.path.isdir(folder_path):
                process_bike_folder(db, folder_path)
                
    db.close()