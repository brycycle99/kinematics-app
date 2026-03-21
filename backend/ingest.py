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
    # Smallest ratio = Low gear (Climbing)
    # Largest ratio = High gear (Descending)
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
        
        # IMMEDIATELY kill any ghost columns caused by trailing semicolons
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        if 'Travel' not in df.columns:
            continue
            
        file_parts_name = file.replace('.csv', '').split('_')
        
        # Handle 2-column files (Anti-squat, Leverage Ratio, etc.)
        if len(df.columns) == 2 and len(file_parts_name) >= 2:
            metric = file_parts_name[1] 
            
            # Map the column based on the gear used
            if len(file_parts_name) == 3:
                gear = file_parts_name[2]
                if gear == gear_low:
                    col_name = f"{metric}_low"
                elif gear == gear_high:
                    col_name = f"{metric}_high"
                else:
                    col_name = f"{metric}_{gear}" 
            else:
                col_name = metric
                
            df.rename(columns={df.columns[1]: col_name}, inplace=True)
            
        # Handle Forces multi-column file to prevent collisions with Geometry
        elif 'Forces' in file:
            # Prefix every column except Travel with 'Force_'
            rename_dict = {col: f"Force_{col}" for col in df.columns if col != 'Travel'}
            df.rename(columns=rename_dict, inplace=True)
            
        # Force the Travel column to be numbers. Text footer becomes NaN.
        df['Travel'] = pd.to_numeric(df['Travel'], errors='coerce')
        
        # Drop any rows where Travel is NaN (deletes the text footer)
        df.dropna(subset=['Travel'], inplace=True)
        
        # Set index and round to 1 decimal place to guarantee perfect alignment
        df.set_index('Travel', inplace=True)
        df.index = df.index.round(1)
        
        # Ensure the rest of the data is numeric too
        df = df.apply(pd.to_numeric, errors='coerce')
        dataframes.append(df)

    if not dataframes:
        print(f"No valid data extracted for {make} {model}.")
        return

    # Merge everything on the Travel index
    merged_df = pd.concat(dataframes, axis=1).reset_index()
    
    # Final check: Drop duplicate columns just in case
    merged_df = merged_df.loc[:, ~merged_df.columns.duplicated()]
    
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
    db.flush() # Generate the ID

    # 6. Save Curve Points
    geometry_cols = ['RW_X', 'RW_Y', 'BB_X', 'BB_Y', 'FW_X', 'FW_Y', 'SHK1_X', 'SHK1_Y', 'SHK2_X', 'SHK2_Y', 'IC_X', 'IC_Y', 'CC_X', 'CC_Y']

    for _, row in merged_df.iterrows():
        
        # Helper to safely grab data
        def get_val(col_name):
            return round(row[col_name], 3) if col_name in merged_df.columns and pd.notna(row[col_name]) else None

        # Package Geometry into JSON
        geom_dict = {
            col: get_val(col) 
            for col in geometry_cols 
            if get_val(col) is not None
        }
        
        # Package Forces into JSON
        force_cols = [c for c in merged_df.columns if str(c).startswith('Force_')]
        forces_dict = {
            col.replace('Force_', ''): get_val(col) 
            for col in force_cols 
            if get_val(col) is not None
        }

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
            forces_data=forces_dict, 
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
    
    # Dynamically find the data folder so this runs from anywhere
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    
    if not os.path.exists(data_dir):
        print(f"Directory {data_dir} does not exist. Create it and add your bike folders.")
    else:
        for folder in os.listdir(data_dir):
            folder_path = os.path.join(data_dir, folder)
            if os.path.isdir(folder_path):
                try:
                    process_bike_folder(db, folder_path)
                except Exception as e:
                    print(f"Error processing {folder}: {e}")
                    db.rollback()
                
    db.close()