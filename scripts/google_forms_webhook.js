/**
 * Badge Generation Webhook for Google Forms
 * Works with spreadsheet-based triggers (On form submit from linked spreadsheet)
 *
 * Setup:
 * 1. Open your Google Form's linked spreadsheet
 * 2. Extensions > Apps Script
 * 3. Paste this entire file
 * 4. Save and set up trigger:
 *    - Triggers (clock icon) > Add Trigger
 *    - Function: onFormSubmit
 *    - Event source: From spreadsheet
 *    - Event type: On form submit
 * 5. Authorize when prompted
 *
 * Testing:
 * - Pre-filled form URL for quick testing:
 *   https://docs.google.com/forms/d/e/1FAIpQLSck2QUCyqc5cZF8iVn539UTwH2NfCHu_rElkYlSwZIoZpGUqQ/viewform?usp=pp_url&entry.1952509218=Frankie+Cleary&entry.321318174=frankievcleary@gmail.com&entry.2083722491=AI+Content+Engineer&entry.2075391414=FBombMedia+LLC&entry.1529364487=Columbus,+OH&entry.1219805484=I'm+a+tech+nerd+who+loves+AI,+cloud,+data,+and+all+things+buzzwords.++I'm+an+entrepreneur+at+heart.++Dabble+in+Spanish+and+chess.++I+have+4+crazy+kids.&entry.193913235=https://www.linkedin.com/in/frankie-cleary/&entry.1259110158=LinkedIn&entry.773960683=frankie-cleary&entry.1500229452=Innovation+%26+Transformation+Council&entry.1196396595=1st&entry.1555989623=Technology&entry.44812202=Individual
 * - Or run testWebhook() function directly to skip the form
 */

// Configuration - UPDATE THESE VALUES
const AZURE_FUNCTION_URL = "https://func-name-tag-gen-66802.azurewebsites.net/api/process-badge";
const EVENT_ID = "cohatch_afterhours";

/**
 * Trigger function - runs when form is submitted
 * Works with spreadsheet trigger (e.namedValues) OR form trigger (e.response)
 */
function onFormSubmit(e) {
  try {
    Logger.log("Form submitted at: " + new Date());
    Logger.log("Event object keys: " + Object.keys(e));

    let payload;

    // Check if this is a spreadsheet trigger (has namedValues) or form trigger (has response)
    if (e.namedValues) {
      Logger.log("Using spreadsheet trigger (namedValues)");
      payload = buildPayloadFromNamedValues(e.namedValues);
    } else if (e.response) {
      Logger.log("Using form trigger (response)");
      payload = buildPayloadFromFormResponse(e.response);
    } else {
      throw new Error("Unknown trigger type - no namedValues or response in event");
    }

    Logger.log("Payload: " + JSON.stringify(payload, null, 2));

    // Send to Azure Function
    const response = sendToAzureFunction(payload);

    Logger.log("Badge generation triggered successfully");
    Logger.log("Response: " + response.getContentText());

  } catch (error) {
    Logger.log("ERROR: " + error.toString());
  }
}

/**
 * Build payload from spreadsheet namedValues (spreadsheet trigger)
 */
function buildPayloadFromNamedValues(namedValues) {
  const payload = {
    event_id: EVENT_ID,
    tags: {}
  };

  // Helper to get first value from array
  function getValue(key) {
    const val = namedValues[key];
    return val && val.length > 0 ? val[0] : "";
  }

  // Log all available columns for debugging
  Logger.log("Available columns: " + Object.keys(namedValues).join(", "));

  // Map column headers to payload fields
  // Update these to match your exact column headers in the spreadsheet
  payload.name = getValue("Full Name") || getValue("Name") || "";
  payload.email = getValue("Email") || getValue("Email Address") || "";
  payload.title = getValue("Job Title") || getValue("Title") || "";
  payload.company = getValue("Company") || getValue("Company Name") || getValue("Organization") || "";
  payload.location = getValue("Location") || getValue("City, State") || "";
  payload.interests = getValue("Interests") || getValue("Hobbies and Interests") || "";
  payload.profile_url = getValue("LinkedIn Profile") || getValue("Profile URL") || "";
  payload.preferred_social_platform = getValue("Preferred Social Platform") || "";
  payload.social_handle = getValue("Social Media Handle") || "";
  payload.pronouns = getValue("Pronouns") || "";

  // Tags - update to match your column headers
  if (getValue("Committee")) payload.tags["Committee"] = getValue("Committee");
  if (getValue("Years as Member")) payload.tags["Years as Member"] = getValue("Years as Member");
  if (getValue("Rep") || getValue("Representative")) payload.tags["Rep"] = getValue("Rep") || getValue("Representative");
  if (getValue("Industry")) payload.tags["Industry"] = getValue("Industry");
  if (getValue("Membership Level")) payload.tags["Membership Level"] = getValue("Membership Level");

  return payload;
}

/**
 * Build payload from form response (form trigger)
 */
function buildPayloadFromFormResponse(formResponse) {
  const itemResponses = formResponse.getItemResponses();
  const payload = {
    event_id: EVENT_ID,
    tags: {}
  };

  itemResponses.forEach(function(itemResponse) {
    const question = itemResponse.getItem().getTitle();
    const answer = itemResponse.getResponse();

    switch(question) {
      case "Full Name":
      case "Name":
        payload.name = answer;
        break;
      case "Email":
      case "Email Address":
        payload.email = answer;
        break;
      case "Job Title":
      case "Title":
        payload.title = answer;
        break;
      case "Company":
      case "Company Name":
      case "Organization":
        payload.company = answer;
        break;
      case "Location":
      case "City, State":
        payload.location = answer;
        break;
      case "Interests":
      case "Hobbies and Interests":
        payload.interests = answer;
        break;
      case "LinkedIn Profile":
      case "Profile URL":
        payload.profile_url = answer;
        break;
      case "Preferred Social Platform":
        payload.preferred_social_platform = answer;
        break;
      case "Social Media Handle":
        payload.social_handle = answer;
        break;
      case "Pronouns":
        payload.pronouns = answer;
        break;
      case "Committee":
        payload.tags["Committee"] = answer;
        break;
      case "Years as Member":
        payload.tags["Years as Member"] = answer;
        break;
      case "Rep":
      case "Representative":
        payload.tags["Rep"] = answer;
        break;
      case "Industry":
        payload.tags["Industry"] = answer;
        break;
      case "Membership Level":
        payload.tags["Membership Level"] = answer;
        break;
      default:
        Logger.log("Unmapped question: " + question);
    }
  });

  return payload;
}

/**
 * Send payload to Azure Function
 */
function sendToAzureFunction(payload) {
  const options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  Logger.log("Sending to: " + AZURE_FUNCTION_URL);

  const response = UrlFetchApp.fetch(AZURE_FUNCTION_URL, options);
  const statusCode = response.getResponseCode();

  if (statusCode !== 200) {
    throw new Error("Azure Function returned status " + statusCode + ": " + response.getContentText());
  }

  return response;
}

/**
 * Test function - run this manually to test the webhook
 */
function testWebhook() {
  const testPayload = {
    event_id: EVENT_ID,
    name: "Test User",
    email: "frankievcleary@gmail.com",
    title: "Software Engineer",
    company: "Test Corp",
    location: "Columbus, OH",
    interests: "coding, hiking",
    tags: {
      "Committee": "Events",
      "Years as Member": "5-9",
      "Rep": "Test",
      "Industry": "Tech",
      "Membership Level": "Pro"
    }
  };

  Logger.log("Testing webhook...");
  const response = sendToAzureFunction(testPayload);
  Logger.log("Test successful!");
  Logger.log("Response: " + response.getContentText());
}
