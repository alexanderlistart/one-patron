import AppKit
import Foundation

guard CommandLine.arguments.count == 5,
      let width = Int(CommandLine.arguments[3]),
      let height = Int(CommandLine.arguments[4]) else {
    fputs("Usage: render_svg.swift input.svg output.png width height\n", stderr)
    exit(2)
}

let inputURL = URL(fileURLWithPath: CommandLine.arguments[1])
let outputURL = URL(fileURLWithPath: CommandLine.arguments[2])

guard let image = NSImage(contentsOf: inputURL) else {
    fputs("Could not load SVG\n", stderr)
    exit(3)
}

guard let bitmap = NSBitmapImageRep(
    bitmapDataPlanes: nil,
    pixelsWide: width,
    pixelsHigh: height,
    bitsPerSample: 8,
    samplesPerPixel: 4,
    hasAlpha: true,
    isPlanar: false,
    colorSpaceName: .deviceRGB,
    bytesPerRow: 0,
    bitsPerPixel: 0
) else {
    fputs("Could not create bitmap\n", stderr)
    exit(4)
}

bitmap.size = NSSize(width: width, height: height)
guard let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
    fputs("Could not create graphics context\n", stderr)
    exit(5)
}

NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = context
context.imageInterpolation = .high
context.cgContext.clear(CGRect(x: 0, y: 0, width: width, height: height))
image.draw(
    in: NSRect(x: 0, y: 0, width: width, height: height),
    from: NSRect(origin: .zero, size: image.size),
    operation: .sourceOver,
    fraction: 1.0,
    respectFlipped: true,
    hints: [.interpolation: NSImageInterpolation.high]
)
context.flushGraphics()
NSGraphicsContext.restoreGraphicsState()

guard let png = bitmap.representation(using: .png, properties: [:]) else {
    fputs("Could not encode PNG\n", stderr)
    exit(6)
}

try png.write(to: outputURL, options: .atomic)
