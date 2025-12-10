import pandas as pd
from datetime import datetime, timedelta

class FlightScheduleParser:
    def __init__(self, file_path: str, month: str = "DEC"):
        self.file_path = file_path
        self.month = month
        self.current_year = datetime.now().year
        self.df = None

        self.date_header_row_index = -1
        self.flight_data_start_row_index = -1

        self.column_to_date = {}
        self.formatted_flights = []

    def load_csv(self):
        self.df = pd.read_csv(
            self.file_path,
            header=None,
            dtype=str,
            keep_default_na=False
        )

    def find_date_header_row(self):
        for index, row in self.df.iterrows():
            if 'day' in str(row[0]).lower():
                self.date_header_row_index = index
                break

        if self.date_header_row_index == -1:
            raise ValueError("Не найден заголовок дней недели ('day').")

    def find_flight_data_start(self):
        start_search_index = self.date_header_row_index + 2

        for index in range(start_search_index, len(self.df)):
            first_col = self.df.iloc[index, 0].strip()

            if first_col != '':
                try:
                    int(first_col)
                except ValueError:
                    self.flight_data_start_row_index = index
                    break

        if self.flight_data_start_row_index == -1:
            raise ValueError("Не найдено начало блока данных рейсов.")

    def extract_date_headers(self):
        date_header_row = self.df.iloc[self.date_header_row_index]
        day_columns = date_header_row[date_header_row.str.strip() != '']

        current_date = None

        for col_idx, cell_value in day_columns.items():
            cell_value = str(cell_value)

            if 'day' in cell_value.lower():
                parts = cell_value.split()
                day_str = next((p for p in parts if p.isdigit()), None)

                if day_str:
                    try:
                        date_str_with_year = f"{day_str.zfill(2)}{self.month}{self.current_year}"
                        current_date = datetime.strptime(date_str_with_year, "%d%b%Y")
                    except ValueError:
                        current_date = None

            if current_date is not None:
                self.column_to_date[col_idx] = current_date

    def extract_flights(self):
        flight_data_df = self.df.iloc[self.flight_data_start_row_index:].copy()
        num_data_rows = 3

        for i in range(0, len(flight_data_df) // num_data_rows):

            flight_row = flight_data_df.iloc[i * num_data_rows]
            route_row = flight_data_df.iloc[i * num_data_rows + 1]
            time_row = flight_data_df.iloc[i * num_data_rows + 2]

            flight_number = flight_row.iloc[0].split(',')[0].strip()

            if not flight_number:
                continue

            for col_idx in range(1, len(flight_row)):
                service_code = f"MFX{flight_row.iloc[col_idx].strip()}"
                current_route = route_row.iloc[col_idx].strip()
                current_time = time_row.iloc[col_idx].strip()

                if current_route != '' and current_time != '':

                    date_of_flight = None
                    col_indices = sorted(self.column_to_date.keys())

                    for col_start in col_indices:
                        if col_idx >= col_start:
                            date_of_flight = self.column_to_date[col_start]
                        else:
                            break

                    if date_of_flight is None:
                        continue

                    is_next_day = '+' in current_time
                    time_str = current_time.replace('+', '').replace(' ', '')

                    flight_date = date_of_flight
                    if is_next_day:
                        flight_date += timedelta(days=1)

                    date_formatted = flight_date.strftime("%d%b").upper()
                    date_line = f"{date_formatted}"

                    flight_line = f"{flight_number} {' ' + service_code if service_code else ''} {current_route.strip()} {time_str}"
                    formatted_line = f"{date_line}\n{flight_line}"

                    self.formatted_flights.append(formatted_line)

    def sort_key(self, line):
        parts = line.split('\n')
        date_code_part = parts[0]
        flight_part = parts[1]

        date_part = date_code_part[:5]

        try:
            date_obj = datetime.strptime(f"{date_part}{self.current_year}", "%d%b%Y")
        except ValueError:
            date_obj = datetime.min

        return (date_obj, flight_part)

    def get_final_output(self):
        unique_flights = sorted(list(set(self.formatted_flights)), key=self.sort_key)
        return "\n".join(unique_flights)