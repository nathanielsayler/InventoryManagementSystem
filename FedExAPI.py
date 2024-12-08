import requests
import json
import base64
import uuid
from datetime import datetime

# FedEx credentials
API_KEY = 'l7308785c9077e4ff58a24578a346723d7'
SECRET_KEY = '1489110f3b56431390f47b6ffb6615c6'
ACCOUNT_NUMBER = '740561073'

# Endpoint URLs
TOKEN_URL = 'https://apis-sandbox.fedex.com/oauth/token'
RATE_URL = 'https://apis-sandbox.fedex.com/rate/v1/rates/quotes'
SHIP_URL = 'https://apis-sandbox.fedex.com/ship/v1/shipments'


def get_access_token(api_key=API_KEY, secret_key=SECRET_KEY):
    # Obtain an OAuth token from FedEx.
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'grant_type': 'client_credentials',
        'client_id': api_key,
        'client_secret': secret_key,
    }
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    return response.json().get('access_token')


def get_rates_and_transit_times(access_token, sender_zip_code=78723, recipient_zip_code=90210, package_weight=1, package_height=1, package_width=1, package_length=1):
    # Request rates and transit times from FedEx.
    headers = {
        'content-type': 'application/json',
        'authorization': f'Bearer {access_token}'
    }
    payload = {
        "accountNumber": {
            "value": ACCOUNT_NUMBER
        },
        "rateRequestControlParameters": {
            "returnTransitTimes": True
        },
        "requestedShipment": {
            "shipper": {
                "address": {
                    "postalCode": str(sender_zip_code),
                    "countryCode": "US",
                    "residential": False
                }
            },
            "recipient": {
                "address": {
                    "postalCode": str(recipient_zip_code),
                    "countryCode": "US",
                    "residential": True
                }
            },
            "pickupType": "USE_SCHEDULED_PICKUP",
            "packagingType": "YOUR_PACKAGING",
            "shipDateStamp": "2024-12-06",
            "requestedPackageLineItems": [
                {
                    "weight": {
                        "units": "LB",
                        "value": str(package_weight)
                    },
                    "dimensions": {
                        "length": str(package_length),
                        "width": str(package_width),
                        "height": str(package_height),
                        "units": "IN"
                    }
                }
            ],
            "rateRequestType": ["ACCOUNT"]
        }
    }

    response = requests.post(RATE_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def parse_rate_response(response):
    # Parse the FedEx API rate response to extract ServiceType, ServiceName (cleaned),
    # TotalNetCharge, whether Saturday delivery is available, and the estimated delivery date.
    options = []
    # Ensure "rateReplyDetails" exists in the response
    if "output" in response and "rateReplyDetails" in response["output"]:
        for detail in response["output"]["rateReplyDetails"]:
            service_type = detail.get("serviceType", "Unknown")
            service_name = detail.get("serviceName", "Unknown").replace("\u00ae", "")  # Remove ® symbol
            total_net_charge = None
            saturday_delivery = False
            commit_date = None

            # Extract totalNetCharge from ratedShipmentDetails
            if "ratedShipmentDetails" in detail:
                for rated_detail in detail["ratedShipmentDetails"]:
                    if "totalNetCharge" in rated_detail:
                        total_net_charge = rated_detail["totalNetCharge"]

            # Extract Saturday delivery information
            if "commit" in detail:
                saturday_delivery = detail["commit"].get("saturdayDelivery", False)
                commit_date = detail["commit"].get("dateDetail", {}).get("dayFormat")

            # Format commitDate if available
            if commit_date:
                try:
                    commit_date = datetime.fromisoformat(commit_date).strftime('%Y-%m-%d %I:%M %p')
                except ValueError:
                    commit_date = "Invalid date format"

            # Append extracted data to options list
            options.append({
                "ServiceType": service_type,
                "ServiceName": service_name,
                "TotalNetCharge": total_net_charge,
                "SaturdayDelivery": saturday_delivery,
                "EstimatedDelivery": commit_date
            })
    return options


def generate_shipping_label(access_token, selected_option, shipper, recipient, package_details, label_file_path):
    # Generate and save a shipping label using the FedEx Ship API.
    print(selected_option)
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
        "x-customer-transaction-id": str(uuid.uuid4()),
        "x-locale": "en_US"
    }

    payload = {
        "labelResponseOptions": "LABEL",
        "mergeLabelDocOption": "NONE",
        "accountNumber": {
            "value": ACCOUNT_NUMBER
        },
        "requestedShipment": {
            "shipAction": "CONFIRM",
            "processingOptionType": "SYNCHRONOUS_ONLY",
            "shipper": shipper,
            "recipients": [recipient],
            "pickupType": "USE_SCHEDULED_PICKUP",
            "serviceType": selected_option["ServiceType"],
            "packagingType": "YOUR_PACKAGING",
            "labelSpecification": {
                "imageType": "PDF",
                "labelStockType": "PAPER_4X6"
            },
            "requestedPackageLineItems": [
                package_details
            ],
            "rateRequestType": ["ACCOUNT"],
            "shippingChargesPayment": {
                "paymentType": "SENDER",
                "payor": {
                    "responsibleParty": {
                        "accountNumber": {
                            "value": ACCOUNT_NUMBER
                        }
                    }
                }
            }
        }
    }

    response = requests.post(SHIP_URL, headers=headers, json=payload)
    response.raise_for_status()

    ship_response = response.json()
    print("Ship Response:", json.dumps(ship_response, indent=4))  # Debugging statement

    if "output" in ship_response and "transactionShipments" in ship_response["output"]:
        transaction = ship_response["output"]["transactionShipments"][0]
        if "pieceResponses" in transaction and len(transaction["pieceResponses"]) > 0:
            piece = transaction["pieceResponses"][0]
            if "packageDocuments" in piece and len(piece["packageDocuments"]) > 0:
                document = piece["packageDocuments"][0]
                if "encodedLabel" in document:
                    # Decode and save the label
                    label_data = document["encodedLabel"]
                    label_bytes = base64.b64decode(label_data)
                    with open(label_file_path, "wb") as label_file:
                        label_file.write(label_bytes)

                    return response
                else:
                    raise ValueError("encodedLabel key is missing in packageDocuments.")
            else:
                raise ValueError("packageDocuments is missing or empty in pieceResponses.")
        else:
            raise ValueError("pieceResponses is missing or empty in transactionShipments.")
    else:
        raise ValueError("Failed to retrieve the shipping label. Check the response for details.")