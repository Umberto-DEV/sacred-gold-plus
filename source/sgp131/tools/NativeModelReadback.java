// Read-only model bridge; supply the pinned Nds4j library on the classpath.
import io.github.turtleisaac.nds4j.g3d.Model;
import io.github.turtleisaac.nds4j.g3d.ModelSet;
import io.github.turtleisaac.nds4j.g3d.DisplayList;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

public final class NativeModelReadback {
    private static String quote(String value) {
        return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
    }
    private static String exactFloats(float[] values) {
        // Float.toString's shortest float representation can change exact DS
        // fixed-point values when JSON is decoded as double (e.g. 256.015625).
        double[] exact = new double[values.length];
        for (int i = 0; i < values.length; i++) exact[i] = values[i];
        return Arrays.toString(exact);
    }
    private static int signed10(int value) { return (value << 22) >> 22; }
    private static String attributes(byte[] raw) {
        StringBuilder colors = new StringBuilder("["), normals = new StringBuilder("["), order = new StringBuilder("[");
        int[] color = null;
        double[] normal = null;
        boolean first = true, colorAfterNormal = false;
        StringBuilder primitives = new StringBuilder("[");
        int type = -1, vertices = 0;
        for (DisplayList.Command c : DisplayList.decodeCommands(raw)) {
            if (c.opcode == 0x40) {
                if (type != -1) throw new IllegalArgumentException("nested primitive");
                type = c.operands[0]; vertices = 0;
            }
            if (c.opcode == 0x41) {
                if (type == -1) throw new IllegalArgumentException("unmatched primitive end");
                if (primitives.length() > 1) primitives.append(',');
                primitives.append("{\"type\":").append(type).append(",\"vertices\":").append(vertices).append('}');
                type = -1;
            }
            int p = c.operands.length == 0 ? 0 : c.operands[0];
            if (c.opcode == 0x20) colorAfterNormal = true;
            if (c.opcode == 0x21) colorAfterNormal = false;
            if (c.opcode == 0x20) color = new int[]{p & 31, (p >> 5) & 31, (p >> 10) & 31};
            if (c.opcode == 0x21) normal = new double[]{signed10(p) / 512.0, signed10(p >> 10) / 512.0, signed10(p >> 20) / 512.0};
            if (c.opcode >= 0x23 && c.opcode <= 0x28) {
                vertices++;
                if (!first) { colors.append(','); normals.append(','); order.append(','); }
                colors.append(color == null ? "null" : Arrays.toString(color));
                normals.append(normal == null ? "null" : Arrays.toString(normal));
                order.append(colorAfterNormal);
                first = false;
            }
        }
        if (type != -1) throw new IllegalArgumentException("unterminated primitive");
        return ",\"primitives\":" + primitives.append(']') + ",\"colors\":" + colors.append(']') + ",\"normals\":" + normals.append(']') + ",\"color_after_normal\":" + order.append(']');
    }
    private static void readback(Path input) throws Exception {
        if(Files.size(input)>0xF000)throw new IllegalArgumentException("model too large");
        byte[] bytes=Files.readAllBytes(input);
        ModelSet set=new ModelSet(bytes);
        if(set.hasEmbeddedTextures() || set.getModels().size()!=1)throw new IllegalArgumentException("model-only required");
        Model model=set.getModels().get(0);
        ByteBuffer raw=ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);
        int start=20+raw.getInt(48);
        StringBuilder json=new StringBuilder("{\"nodes\":"+model.getNodeCount()+",\"scale\":"+model.getPositionScale()
            +",\"header_vertices\":"+model.getExpectedVertexCount()+",\"vertices\":"+model.getVertexCount()
            +",\"header_counts\":"+Arrays.toString(new int[]{raw.getShort(start+36)&65535,raw.getShort(start+38)&65535,raw.getShort(start+40)&65535,raw.getShort(start+42)&65535})
            +",\"header_bounds\":"+Arrays.deepToString(model.getHeaderBoundingBox())
            +",\"decoded_bounds\":"+Arrays.deepToString(model.getDecodedBoundingBox())+",\"meshes\":[");
        boolean first=true;
        for(Model.Mesh mesh:model.getMeshes()) {
            if(!first)json.append(',');first=false;
            Model.Material mat=mesh.getMaterial();
            json.append("{\"name\":").append(quote(mesh.getName())).append(",\"node\":").append(mesh.getNodeIndex())
                .append(",\"material\":").append(quote(mat.getName())).append(",\"texture\":").append(quote(mat.getTextureName()))
                .append(",\"palette\":").append(quote(mat.getPaletteName()))
                .append(",\"positions\":").append(exactFloats(mesh.getPositions()))
                .append(",\"texcoords\":").append(exactFloats(mesh.getTexcoords()))
                .append(",\"triangles\":").append(Arrays.toString(mesh.getTriangleIndices()))
                .append(attributes(mesh.getRawDisplayList())).append('}');
        }
        System.out.println(json.append("]}"));
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 2 || !args[0].equals("readback")) {
            throw new IllegalArgumentException("readback model");
        }
        readback(Path.of(args[1]));
    }
}
