import Foundation
import Vision
import AppKit

struct RecognizedItem: Codable {
    let text: String
    let confidence: Float
    let x: Double
    let y: Double
    let width: Double
    let height: Double
}

guard CommandLine.arguments.count > 1 else {
    fputs("Usage: vision_ocr <image_path>\n", stderr)
    exit(1)
}

let imagePath = CommandLine.arguments[1]
guard let image = NSImage(contentsOfFile: imagePath),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    fputs("Failed to load image: \(imagePath)\n", stderr)
    exit(1)
}

let requestHandler = VNImageRequestHandler(cgImage: cgImage, options: [:])
var items: [RecognizedItem] = []

let request = VNRecognizeTextRequest { request, error in
    guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
    for obs in observations {
        guard let candidate = obs.topCandidates(1).first else { continue }
        let box = obs.boundingBox
        items.append(RecognizedItem(
            text: candidate.string,
            confidence: candidate.confidence,
            x: box.origin.x,
            y: box.origin.y,
            width: box.size.width,
            height: box.size.height
        ))
    }
}

request.recognitionLevel = .accurate
request.usesLanguageCorrection = false
if #available(macOS 12.0, *) {
    request.automaticallyDetectsLanguage = true
}

do {
    try requestHandler.perform([request])
    let encoder = JSONEncoder()
    encoder.outputFormatting = .prettyPrinted
    let data = try encoder.encode(items)
    if let jsonStr = String(data: data, encoding: .utf8) {
        print(jsonStr)
    }
} catch {
    fputs("OCR Error: \(error)\n", stderr)
    exit(1)
}
